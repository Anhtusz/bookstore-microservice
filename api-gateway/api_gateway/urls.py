from django.contrib import admin
from django.urls import path, re_path
from .views import book_list, view_cart, proxy_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('books/', book_list),
    path('cart/<int:customer_id>/', view_cart),
    re_path(r'^api/(?P<service_name>[^/]+)/(?P<path>.*)$', proxy_view),
]