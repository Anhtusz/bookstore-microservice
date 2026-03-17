import os
import requests
from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

BOOK_SERVICE_URL = os.environ.get("BOOK_SERVICE_URL", "http://book-service:8000")
CART_SERVICE_URL = os.environ.get("CART_SERVICE_URL", "http://cart-service:8000")

def book_list(request):
    try:
        r = requests.get(f"{BOOK_SERVICE_URL}/books/")
        return render(request, "books.html", {"books": r.json()})
    except Exception as e:
        return render(request, "books.html", {"books": [], "error": str(e)})


def view_cart(request, customer_id):
    try:
        r = requests.get(f"{CART_SERVICE_URL}/carts/{customer_id}/")
        return render(request, "cart.html", {"items": r.json()})
    except Exception as e:
        return render(request, "cart.html", {"items": [], "error": str(e)})

SERVICE_MAP = {
    'staff': 'staff-service:8000',
    'manager': 'manager-service:8000',
    'customer': 'customer-service:8000',
    'catalog': 'catalog-service:8000',
    'book': 'book-service:8000',
    'cart': 'cart-service:8000',
    'order': 'order-service:8000',
    'pay': 'pay-service:8000',
    'ship': 'ship-service:8000',
    'comment-rate': 'comment-rate-service:8000',
    'recommender-ai': 'recommender-ai-service:8000',
}

@csrf_exempt
def proxy_view(request, service_name, path):
    if service_name not in SERVICE_MAP:
        return JsonResponse({"error": "Service not found"}, status=404)
        
    target_host = SERVICE_MAP[service_name]
    # Ensure no double slashes, but keep trailing slash if it exists
    target_url = f"http://{target_host}/api/{path}"
    print(f"PROXYING: {request.method} {request.path} -> {target_url}")
    
    if request.META.get('QUERY_STRING'):
        target_url += f"?{request.META.get('QUERY_STRING')}"

    try:
        response = requests.request(
            method=request.method,
            url=target_url,
            headers={k: v for k, v in request.headers.items() if k.lower() != 'host'},
            data=request.body,
            cookies=request.COOKIES,
            allow_redirects=False,
        )
        
        return HttpResponse(
            content=response.content,
            status=response.status_code,
            content_type=response.headers.get('Content-Type', 'application/json')
        )
    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=502)