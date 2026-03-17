from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, GenreViewSet, CatalogItemViewSet

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'genres', GenreViewSet, basename='genre')
router.register(r'items', CatalogItemViewSet, basename='catalogitem')

urlpatterns = [
    path('', include(router.urls)),
]
