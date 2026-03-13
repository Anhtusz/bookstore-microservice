from django.contrib import admin
from django.urls import path
from .views import book_list, view_cart

urlpatterns = [
    path('admin/', admin.site.urls),
    path('books/', book_list),
    path('cart/<int:customer_id>/', view_cart),
]