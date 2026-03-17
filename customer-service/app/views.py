from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.hashers import make_password, check_password
from .models import Customer
from .serializers import CustomerSerializer
import requests
import os

CART_SERVICE_URL = os.environ.get("CART_SERVICE_URL", "http://cart-service:8000")


class CustomerListCreate(APIView):
    """Register a new customer."""

    def get(self, request):
        customers = Customer.objects.all()
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()

        # Hash password before saving
        raw_password = data.get('password', '')
        if raw_password:
            data['password'] = make_password(raw_password)

        serializer = CustomerSerializer(data=data)
        if serializer.is_valid():
            customer = serializer.save()

            # Auto-create cart
            try:
                requests.post(
                    f"{CART_SERVICE_URL}/api/carts/",
                    json={"customer_id": customer.id},
                    timeout=5
                )
            except Exception as e:
                print(f"Failed to create cart for customer {customer.id}: {e}")

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerLogin(APIView):
    """Authenticate an existing customer by email + password."""

    def post(self, request):
        email = request.data.get('email', '').strip()
        raw_password = request.data.get('password', '')

        try:
            customer = Customer.objects.get(email=email)
        except Customer.DoesNotExist:
            return Response(
                {"detail": "No account found with this email."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not check_password(raw_password, customer.password):
            return Response(
                {"detail": "Incorrect password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        serializer = CustomerSerializer(customer)
        return Response(serializer.data, status=status.HTTP_200_OK)