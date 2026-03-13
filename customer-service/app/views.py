from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Customer
from .serializers import CustomerSerializer
import requests

# Nếu chạy LOCAL
CART_SERVICE_URL = "http://cart-service:8000"


class CustomerListCreate(APIView):

    def get(self, request):
        customers = Customer.objects.all()
        serializer = CustomerSerializer(customers, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CustomerSerializer(data=request.data)

        if serializer.is_valid():
            customer = serializer.save()

            # Gọi sang Cart Service sau khi tạo customer
            requests.post(
                f"{CART_SERVICE_URL}/",
                json={"customer_id": customer.id}
            )

            return Response(serializer.data)

        return Response(serializer.errors)