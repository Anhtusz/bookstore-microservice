from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Transaction
from rest_framework import serializers

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer

    def create(self, request, *args, **kwargs):
        # Stub logic: In reality, calling Stripe/PayPal API
        # would happen here, generating an external `transaction_id`.
        data = request.data.copy()
        
        # Simulate payment API success
        data['status'] = 'SUCCESS'
        data['transaction_id'] = 'STUB_TXN_00123'
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
