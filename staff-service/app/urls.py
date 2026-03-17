from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookProxyViewSet, CategoryProxyViewSet, OrderProxyViewSet

router = DefaultRouter()
router.register(r'manage-books', BookProxyViewSet, basename='manage-books')
router.register(r'manage-categories', CategoryProxyViewSet, basename='manage-categories')
router.register(r'manage-orders', OrderProxyViewSet, basename='manage-orders')

urlpatterns = [
    path('', include(router.urls)),
]
