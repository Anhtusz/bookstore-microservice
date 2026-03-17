from rest_framework import serializers
from .models import Book

class BookSerializer(serializers.ModelSerializer):
    stock_status = serializers.ReadOnlyField()

    class Meta:
        model = Book
        fields = '__all__'