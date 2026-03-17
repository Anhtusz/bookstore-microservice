from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StoreAnalyticsViewSet

router = DefaultRouter()
router.register(r'analytics', StoreAnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
]
