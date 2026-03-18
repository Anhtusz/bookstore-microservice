import os
import random
import requests
from collections import Counter

from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Recommendation
from rest_framework import serializers

BOOK_SVC   = os.environ.get("BOOK_SERVICE_URL",   "http://book-service:8000").rstrip('/')
CATALOG_SVC = os.environ.get("CATALOG_SERVICE_URL", "http://catalog-service:8000").rstrip('/')
ORDER_SVC  = os.environ.get("ORDER_SERVICE_URL",  "http://order-service:8000").rstrip('/')


def _get_books():
    r = requests.get(f"{BOOK_SVC}/api/books/", timeout=5)
    return r.json() if r.status_code == 200 else []


def _get_catalog_items():
    r = requests.get(f"{CATALOG_SVC}/api/items/", timeout=5)
    return r.json() if r.status_code == 200 else []


def _get_orders():
    r = requests.get(f"{ORDER_SVC}/api/orders/", timeout=5)
    return r.json() if r.status_code == 200 else []


class RecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recommendation
        fields = '__all__'


class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer

    # ── 1. Random suggest (original, kept for backwards compat) ──────────────
    @action(detail=False, methods=['get'])
    def suggest(self, request):
        """Return up to 4 random books. Used as a fallback."""
        try:
            books = _get_books()
            suggested = random.sample(books, min(4, len(books)))
            return Response(suggested)
        except Exception as e:
            return Response([], status=status.HTTP_200_OK)

    # ── 2. Category-based recommend ──────────────────────────────────────────
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Given ?book_id=<id>, return up to 6 books in the same category.
        Also accepts ?category_id=<id> directly.
        """
        book_id     = request.query_params.get('book_id')
        category_id = request.query_params.get('category_id')

        try:
            catalog_items = _get_catalog_items()

            # Resolve category_id from book_id if not provided
            if not category_id and book_id:
                for item in catalog_items:
                    if str(item.get('book_id')) == str(book_id):
                        category_id = item.get('category')
                        break

            if not category_id:
                return Response([])

            # Find book_ids in that category (excluding current book)
            related_book_ids = {
                str(item['book_id'])
                for item in catalog_items
                if str(item.get('category')) == str(category_id)
                   and str(item.get('book_id')) != str(book_id)
            }

            # Fetch books, filter to related
            books = _get_books()
            related = [b for b in books if str(b['id']) in related_book_ids]
            return Response(random.sample(related, min(6, len(related))))

        except Exception as e:
            return Response([], status=status.HTTP_200_OK)

    # ── 3. Popularity-based (most ordered) ───────────────────────────────────
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """
        Return up to 8 most-ordered books, based on order-service data.
        Each order's 'items' list contains book_ids.
        """
        limit = int(request.query_params.get('limit', 8))
        try:
            orders = _get_orders()
            book_counter = Counter()

            for order in orders:
                # order items may be a list of {book_id, quantity} dicts
                items = order.get('items') or []
                for item in items:
                    bid = item.get('book_id') or item.get('book')
                    qty = item.get('quantity', 1)
                    if bid:
                        book_counter[str(bid)] += qty

            if not book_counter:
                # fallback: return random books
                books = _get_books()
                return Response(random.sample(books, min(limit, len(books))))

            top_ids = {bid for bid, _ in book_counter.most_common(limit)}
            books = _get_books()
            popular = [b for b in books if str(b['id']) in top_ids]
            # Sort by order count descending
            popular.sort(key=lambda b: book_counter.get(str(b['id']), 0), reverse=True)
            return Response(popular[:limit])

        except Exception as e:
            return Response([], status=status.HTTP_200_OK)

    # ── 4. Session-based: personalised based on recently-viewed books ────────
    @action(detail=False, methods=['post'])
    def for_session(self, request):
        """
        POST body: { "viewed_book_ids": [id1, id2, ...] }
        Returns books that share categories with recently viewed books,
        weighted by how often each category appears in the history.
        """
        viewed_ids = request.data.get('viewed_book_ids', [])
        if not viewed_ids:
            return Response([])

        try:
            catalog_items = _get_catalog_items()

            # Map book_id -> category_id
            cat_map = {str(item['book_id']): item.get('category') for item in catalog_items}

            # Count category appearances in viewed history
            cat_counter = Counter()
            for bid in viewed_ids:
                cat = cat_map.get(str(bid))
                if cat:
                    cat_counter[str(cat)] += 1

            if not cat_counter:
                return Response([])

            # Collect eligible books (not already viewed)
            viewed_set = {str(v) for v in viewed_ids}
            books = _get_books()

            scored = []
            for book in books:
                bid = str(book['id'])
                if bid in viewed_set:
                    continue
                cat = cat_map.get(bid)
                weight = cat_counter.get(str(cat), 0) if cat else 0
                if weight > 0:
                    scored.append((weight, book))

            # Sort by weight, shuffle within same weight, return top 6
            scored.sort(key=lambda x: x[0], reverse=True)
            result = [b for _, b in scored[:12]]
            random.shuffle(result)
            return Response(result[:6])

        except Exception as e:
            return Response([], status=status.HTTP_200_OK)
