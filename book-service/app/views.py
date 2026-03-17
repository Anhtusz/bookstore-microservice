from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Book
from .serializers import BookSerializer

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    @action(detail=True, methods=['post'])
    def reduce_stock(self, request, pk=None):
        book = self.get_object()
        try:
            quantity = int(request.data.get('quantity', 1))
        except (TypeError, ValueError):
            quantity = 1
            
        if book.stock >= quantity:
            book.stock -= quantity
            book.save()
            return Response({'status': 'stock reduced', 'remaining': book.stock})
        return Response({'error': 'Insufficient stock'}, status=status.HTTP_400_BAD_REQUEST)