from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Category, Genre, CatalogItem
from rest_framework import serializers

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = '__all__'

class CatalogItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogItem
        fields = '__all__'

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer

class CatalogItemViewSet(viewsets.ModelViewSet):
    queryset = CatalogItem.objects.all()
    serializer_class = CatalogItemSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['category', 'genres']
    search_fields = ['keywords', 'category__name', 'genres__name']
    lookup_field = 'book_id'

    def update(self, request, *args, **kwargs):
        book_id = kwargs.get('book_id')
        
        # Build safe defaults using category_id (FK field) not category (object)
        category_val = request.data.get('category')
        defaults = {}
        if category_val:
            try:
                defaults['category_id'] = int(category_val)
            except (ValueError, TypeError):
                pass
        
        keywords = request.data.get('keywords', '')
        if keywords:
            defaults['keywords'] = keywords

        instance, created = CatalogItem.objects.update_or_create(
            book_id=book_id,
            defaults=defaults
        )
        serializer = self.get_serializer(instance)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
        )
