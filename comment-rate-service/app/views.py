import os
import requests
from rest_framework import viewsets, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from .models import Review
from rest_framework import serializers
from rest_framework.response import Response

BOOK_SERVICE_URL_ENV = os.environ.get("BOOK_SERVICE_URL", "http://book-service:8000")
BOOK_SERVICE_URL = f"{BOOK_SERVICE_URL_ENV.rstrip('/')}/api/books/"

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    
    # Optional: Basic filtering logic to get reviews for a specific book
    def get_queryset(self):
        queryset = Review.objects.all()
        book_id = self.request.query_params.get('book_id', None)
        if book_id is not None:
            queryset = queryset.filter(book_id=book_id)
        return queryset

    def create(self, request, *args, **kwargs):
        book_id = request.data.get('book_id')
        if book_id is not None:
            try:
                r = requests.get(f"{BOOK_SERVICE_URL}{book_id}/")
                if r.status_code == 404:
                    return Response({"error": "Book not found in catalog."}, status=status.HTTP_400_BAD_REQUEST)
            except requests.exceptions.RequestException:
                pass # Proceed anyway if book-service is down
            
        return super().create(request, *args, **kwargs)
