from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
import requests

BOOK_SERVICE_URL = "http://book-service:8000"


# Tạo cart khi customer được tạo
class CartCreate(APIView):

    def post(self, request):
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors)


# Thêm sản phẩm vào cart
class AddCartItem(APIView):

    def post(self, request):
        book_id = request.data["book_id"]

        # Kiểm tra book có tồn tại không
        r = requests.get(f"{BOOK_SERVICE_URL}/books/")
        books = r.json()

        if not any(b["id"] == book_id for b in books):
            return Response({"error": "Book not found"})

        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors)


# Xem cart theo customer_id
class ViewCart(APIView):

    def get(self, request, customer_id):
        cart = Cart.objects.get(customer_id=customer_id)
        items = CartItem.objects.filter(cart=cart)
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data)