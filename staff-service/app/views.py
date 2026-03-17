from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import requests
import os

# Book service base host
_BOOK_HOST = os.environ.get('BOOK_SERVICE_URL', 'http://book-service:8000').rstrip('/')
BOOK_URL = f"{_BOOK_HOST}/api/books/"

_CATALOG_HOST = os.environ.get('CATALOG_SERVICE_URL', 'http://catalog-service:8000').rstrip('/')
CAT_URL = f"{_CATALOG_HOST}/api/categories/"

SHIP_URL = f"{_BOOK_HOST.replace('book-service', 'order-service')}/api/orders/"

class BaseProxyViewSet(viewsets.ViewSet):
    target_url = None

    def _proxy(self, method, url, data=None):
        try:
            resp = requests.request(method, url, json=data, timeout=5)
            if resp.status_code == 204:
                return Response(status=status.HTTP_204_NO_CONTENT)
            try:
                return Response(resp.json(), status=resp.status_code)
            except:
                return Response(status=resp.status_code)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)

    def list(self, request):
        return self._proxy('GET', self.target_url)

    def create(self, request):
        return self._proxy('POST', self.target_url, request.data)

    def retrieve(self, request, pk=None):
        return self._proxy('GET', f"{self.target_url}{pk}/")

    def update(self, request, pk=None):
        return self._proxy('PUT', f"{self.target_url}{pk}/", request.data)

    def destroy(self, request, pk=None):
        return self._proxy('DELETE', f"{self.target_url}{pk}/")

class OrderProxyViewSet(BaseProxyViewSet):
    target_url = SHIP_URL

    @action(detail=True, methods=['post'])
    def confirm_shipment(self, request, pk=None):
        return self._proxy('POST', f"{self.target_url}{pk}/confirm_shipment/", request.data)

class BookProxyViewSet(BaseProxyViewSet):
    target_url = BOOK_URL

    def create(self, request):
        resp = self._proxy('POST', self.target_url, request.data)
        if resp.status_code == 201:
            book_data = resp.data
            book_id = book_data.get('id')
            category_id = request.data.get('category') or request.data.get('category_id')
            
            if book_id and category_id:
                catalog_data = {
                    'book_id': book_id,
                    'category': category_id,
                    'keywords': f"{book_data.get('title', '')} {book_data.get('author', '')}"
                }
                try:
                    requests.post(f"{_CATALOG_HOST}/api/items/", json=catalog_data, timeout=5)
                except Exception as e:
                    print("Failed to catalog item", e)
        return resp

class CategoryProxyViewSet(BaseProxyViewSet):
    target_url = CAT_URL
