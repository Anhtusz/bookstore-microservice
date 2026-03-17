from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Shipment
from rest_framework import serializers

class ShipmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shipment
        fields = '__all__'

class ShipmentViewSet(viewsets.ModelViewSet):
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer

    def create(self, request, *args, **kwargs):
        # Generate dummy tracking details
        data = request.data.copy()
        data['tracking_number'] = 'TRK-1Z999999999'
        data['shipping_label_url'] = 'http://example.com/labels/TRK-1Z999999999.pdf'
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
