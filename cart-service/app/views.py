from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Cart, CartItem
from .serializers import CartSerializer, CartItemSerializer
import os
import requests

_BOOK_HOST = os.environ.get("BOOK_SERVICE_URL", "http://book-service:8000").rstrip('/')
BOOK_SERVICE_URL = f"{_BOOK_HOST}/api/books/"


class CartCreate(APIView):
    """Create a cart for a newly registered customer."""

    def post(self, request):
        serializer = CartSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AddCartItem(APIView):
    """Add a book to a customer's cart."""

    def post(self, request):
        book_id = request.data.get("book_id")
        if not book_id:
            return Response({"error": "book_id is required"}, status=400)

        # Verify the book exists in book-service
        try:
            target_url = f"{BOOK_SERVICE_URL}{book_id}/"
            print(f"CART-SERVICE VALIDATING BOOK: {target_url}")
            r = requests.get(target_url, timeout=5)
            print(f"BOOK-SERVICE RESPONSE: {r.status_code}")
            if r.status_code == 404:
                return Response({"error": f"Book {book_id} not found"}, status=404)
            if r.status_code != 200:
                print(f"BOOK-SERVICE ERROR BODY: {r.text[:200]}")
                return Response({"error": "Book service error"}, status=502)
        except requests.exceptions.RequestException as e:
            print(f"BOOK-SERVICE UNREACHABLE: {e}")
            return Response({"error": f"Cannot reach book-service: {str(e)}"}, status=502)

        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ViewCart(APIView):
    """Get all items in a customer's cart."""

    def get(self, request, customer_id):
        try:
            cart = Cart.objects.get(customer_id=customer_id)
        except Cart.DoesNotExist:
            return Response({"error": "Cart not found"}, status=404)

        items = CartItem.objects.filter(cart=cart)
        serializer = CartItemSerializer(items, many=True)
        return Response(serializer.data)


class CartItemDetail(APIView):
    """Update quantity or delete a single cart item."""

    def get_object(self, pk):
        try:
            return CartItem.objects.get(pk=pk)
        except CartItem.DoesNotExist:
            return None

    def put(self, request, pk):
        cart_item = self.get_object(pk)
        if not cart_item:
            return Response({"error": "Not found"}, status=404)

        serializer = CartItemSerializer(cart_item, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        cart_item = self.get_object(pk)
        if not cart_item:
            return Response({"error": "Not found"}, status=404)
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)