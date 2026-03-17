from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Recommendation
from rest_framework import serializers

class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = '__all__'

class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer

    @action(detail=False, methods=['get'])
    def suggest(self, request):
        import os
        import requests
        import random
        
        book_service_url = os.environ.get("BOOK_SERVICE_URL", "http://book-service:8000").rstrip('/')
        try:
            r = requests.get(f"{book_service_url}/api/books/", timeout=5)
            if r.status_code == 200:
                books = r.json()
                if len(books) > 4:
                    suggested = random.sample(books, 4)
                else:
                    suggested = books
                return Response(suggested, status=status.HTTP_200_OK)
            return Response([], status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Failed to generate recommendations", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
