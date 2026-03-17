from django.contrib import admin
from django.urls import path, re_path
from django.http import HttpResponse
from app.views import CartCreate, AddCartItem, ViewCart, CartItemDetail

def debug_request(request, path):
    print(f"DEBUG REQUEST: Method={request.method}, Path={request.path}")
    return HttpResponse(f"Not Found Debug: {request.path}", status=404)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/carts/', CartCreate.as_view()),
    path('api/cart-items/', AddCartItem.as_view()),
    path('api/cart-items/<int:pk>/', CartItemDetail.as_view()),
    path('api/carts/<int:customer_id>/', ViewCart.as_view()),
    re_path(r'^(?P<path>.*)$', debug_request),
]