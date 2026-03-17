from rest_framework import viewsets
from .models import StoreAnalytics
from rest_framework import serializers

class StoreAnalyticsSerializer(serializers.ModelSerializer):
    class Meta:
        model = StoreAnalytics
        fields = '__all__'

class StoreAnalyticsViewSet(viewsets.ModelViewSet):
    queryset = StoreAnalytics.objects.all()
    serializer_class = StoreAnalyticsSerializer
