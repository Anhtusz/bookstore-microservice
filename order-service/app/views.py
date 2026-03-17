import os
import requests
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Order, OrderItem
from rest_framework import serializers

CART_SERVICE_URL = os.environ.get("CART_SERVICE_URL", "http://cart-service:8000").rstrip('/')
BOOK_SERVICE_URL = os.environ.get("BOOK_SERVICE_URL", "http://book-service:8000").rstrip('/')
SHIP_SERVICE_URL = os.environ.get("SHIP_SERVICE_URL", "http://ship-service:8000").rstrip('/')
PAY_SERVICE_URL = os.environ.get("PAY_SERVICE_URL", "http://pay-service:8000").rstrip('/')

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = '__all__'

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        return queryset

    def create(self, request, *args, **kwargs):
        customer_id = request.data.get('customer_id')
        customer_name = request.data.get('customer_name', '')
        customer_phone = request.data.get('customer_phone', '')
        shipping_address = request.data.get('shipping_address', '')
        payment_method = request.data.get('payment_method', 'COD')

        if not customer_id:
            return Response({"error": "customer_id required"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Fetch Cart
        try:
            cart_resp = requests.get(f"{CART_SERVICE_URL}/api/carts/{customer_id}/")
            if cart_resp.status_code != 200:
                return Response({"error": "Failed to fetch cart"}, status=cart_resp.status_code)
            cart_items = cart_resp.json()
            if not cart_items:
                return Response({"error": "Cart is empty"}, status=status.HTTP_400_BAD_REQUEST)
        except requests.exceptions.RequestException:
            return Response({"error": "Failed to connect to cart service"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 2. Fetch books for pricing
        try:
            books_resp = requests.get(f"{BOOK_SERVICE_URL}/api/books/")
            books = {b['id']: b for b in books_resp.json()} if books_resp.status_code == 200 else {}
        except:
            books = {}

        total_price = 0
        for item in cart_items:
            price = float(books.get(item['book_id'], {}).get('price', 10.0))
            total_price += price * item['quantity']

        # 3. Create Order in WAITING_CONFIRMATION state initially
        order = Order.objects.create(
            customer_id=customer_id,
            customer_name=customer_name,
            customer_phone=customer_phone,
            shipping_address=shipping_address,
            payment_method=payment_method,
            total_price=total_price,
            status='WAITING_CONFIRMATION'
        )

        # 3.5 Process Payment if BANK
        if payment_method == 'BANK':
            try:
                pay_data = {
                    "order_id": order.id,
                    "amount": str(total_price),
                    "payment_method": "BANK"
                }
                pay_resp = requests.post(f"{PAY_SERVICE_URL}/api/transactions/", json=pay_data, timeout=5)
                if pay_resp.status_code == 201:
                    order.status = 'PAID'
                    order.save()
                else:
                    order.status = 'PAYMENT_FAILED'
                    order.save()
            except Exception:
                order.status = 'PAYMENT_FAILED'
                order.save()

        for item in cart_items:
            price = float(books.get(item['book_id'], {}).get('price', 10.0))
            OrderItem.objects.create(order=order, book_id=item['book_id'], quantity=item['quantity'], price=price)
            # Reduce stock in book-service
            try:
                requests.post(f"{BOOK_SERVICE_URL}/api/books/{item['book_id']}/reduce_stock/", json={"quantity": item['quantity']})
            except:
                pass

        # 4. Clear cart
        for item in cart_items:
            try:
                requests.delete(f"{CART_SERVICE_URL}/api/cart-items/{item['id']}/")
            except:
                pass

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def confirm_shipment(self, request, pk=None):
        order = self.get_object()
        if order.status != 'WAITING_CONFIRMATION':
            return Response({"error": f"Cannot confirm shipment for order in {order.status} status"}, status=status.HTTP_400_BAD_REQUEST)

        # Update status to SHIPPING
        order.status = 'SHIPPING'
        order.save()

        # Trigger ship-service
        try:
            requests.post(f"{SHIP_SERVICE_URL}/api/shipments/", json={
                "order_id": order.id,
                "address": order.shipping_address
            })
        except:
            pass # Continue even if notification fails

        return Response(OrderSerializer(order).data)
