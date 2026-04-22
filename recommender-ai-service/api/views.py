import os
from typing import Any, Dict, List

import json
import torch
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from graph.neo4j_client import Neo4jRecommender
from models.sequence_models import BehaviorBiLSTM, BehaviorLSTM, BehaviorRNN
from rag.generator import RAGGenerator
from rag.retriever import RAGRetriever


base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, "data")
model_path = os.path.join(base_dir, "models", "model_best.pt")

NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://db-neo4j:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

retriever = None
generator = None
ml_model = None
action_encoder_classes: List[str] = []


def get_retriever():
    global retriever
    if retriever is None:
        retriever = RAGRetriever(data_dir)
    return retriever


def get_generator():
    global generator
    if generator is None:
        generator = RAGGenerator()
    return generator


def get_ml_model():
    global ml_model, action_encoder_classes
    if ml_model is not None:
        return ml_model

    if not os.path.exists(model_path):
        return None

    checkpoint = torch.load(model_path, map_location=torch.device("cpu"), weights_only=False)
    num_actions = checkpoint["num_actions"]
    model_name = checkpoint["model_name"]
    action_encoder_classes = [str(x) for x in checkpoint["encoder_classes"]]

    if model_name == "RNN":
        model = BehaviorRNN(num_actions)
    elif model_name == "LSTM":
        model = BehaviorLSTM(num_actions)
    else:
        model = BehaviorBiLSTM(num_actions)

    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()
    ml_model = model
    return ml_model


def _load_seed_books() -> List[Dict[str, Any]]:
    with open(os.path.join(data_dir, "books.json"), "r", encoding="utf-8") as file:
        return json.load(file)


def _normalize_book_payload(books: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
    cleaned = []
    for book in books[:limit]:
        cleaned.append(
            {
                "id": book.get("id"),
                "title": book.get("title"),
                "author": book.get("author"),
                "description": book.get("description"),
                "price": book.get("price"),
                "stock": book.get("stock"),
                "image_url": book.get("image_url"),
                "category_name": book.get("category_name"),
            }
        )
    return cleaned


class RecommendView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")
        query = request.data.get("query", "")

        if not user_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        graph_client = Neo4jRecommender(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        try:
            behavior = graph_client.get_user_behavior(int(user_id))
        finally:
            graph_client.close()

        retrieved_books = get_retriever().hybrid_search(query or "popular books", top_k=5)
        explanation = get_generator().generate_recommendation_response(
            user_query=query or "popular books",
            retrieved_books=retrieved_books,
            graph_context=f"User behavior: {behavior[:8]}",
        )
        return Response(
            {
                "recommended_books": retrieved_books,
                "explanation": explanation,
            },
            status=status.HTTP_200_OK,
        )


class ChatView(APIView):
    def post(self, request):
        query = (request.data.get("query") or request.data.get("message") or "").strip()
        raw_user_id = request.data.get("user_id")
        user_id = int(raw_user_id) if str(raw_user_id).isdigit() else None

        if not query:
            return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)

        graph_client = Neo4jRecommender(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        try:
            graph_contexts, sources = graph_client.get_chat_context(query=query, user_id=user_id, limit=6)
        finally:
            graph_client.close()

        semantic_contexts = []
        try:
            semantic_contexts = get_retriever().hybrid_search(query, top_k=3)
        except Exception:
            semantic_contexts = []

        result = get_generator().graph_rag_chat(
            query=query,
            graph_contexts=graph_contexts,
            semantic_contexts=semantic_contexts,
        )

        answer = result.get("answer") or "I don't know based on the available context."
        return Response(
            {
                "answer": answer,
                "sources": sources,
                "context": result.get("used_context", []),
                "retrieval_mode": "graph_rag",
            },
            status=status.HTTP_200_OK,
        )


class PredictView(APIView):
    def post(self, request):
        sequence = request.data.get("sequence")
        if not sequence or not isinstance(sequence, list):
            return Response({"error": "Valid sequence list is required"}, status=status.HTTP_400_BAD_REQUEST)

        model = get_ml_model()
        if not model or not action_encoder_classes:
            return Response({"error": "ML model not available"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        encoded_seq = []
        for action in sequence:
            if action in action_encoder_classes:
                encoded_seq.append(action_encoder_classes.index(action))
            else:
                encoded_seq.append(0)

        seq_tensor = torch.tensor([encoded_seq], dtype=torch.long)
        with torch.no_grad():
            outputs = model(seq_tensor)
            predicted_idx = int(torch.argmax(outputs, 1).item())

        predicted_action = action_encoder_classes[predicted_idx]

        raw_user_id = request.data.get("user_id")
        if str(raw_user_id).isdigit():
            graph_client = Neo4jRecommender(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
            try:
                graph_client.ensure_constraints()
                with graph_client.driver.session() as session:
                    session.run(
                        """
                        MERGE (u:User {id: $uid})
                        WITH u
                        OPTIONAL MATCH (u)-[old:HAS_LABEL]->(:Label)
                        DELETE old
                        WITH u
                        MERGE (l:Label {name: $label})
                        MERGE (u)-[:HAS_LABEL]->(l)
                        """,
                        uid=int(raw_user_id),
                        label=str(predicted_action),
                    )
            finally:
                graph_client.close()

        return Response(
            {
                "sequence": sequence,
                "predicted_next_action": predicted_action,
            },
            status=status.HTTP_200_OK,
        )


VALID_ACTIONS = {"view", "click", "add_to_cart", "purchase", "remove_cart", "search", "review"}


class TrackEventView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")
        product_id = request.data.get("product_id")
        action = request.data.get("action")

        if not all([user_id, product_id, action]):
            return Response(
                {"error": "user_id, product_id, and action are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if action not in VALID_ACTIONS:
            return Response(
                {"error": f"Invalid action. Must be one of: {', '.join(sorted(VALID_ACTIONS))}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from api.models import BehaviorEvent

        event = BehaviorEvent.objects.create(
            user_id=int(user_id),
            product_id=int(product_id),
            action=action,
            session_id=request.data.get("session_id", ""),
        )

        return Response({"id": event.id, "status": "tracked"}, status=status.HTTP_201_CREATED)


class TrackBatchView(APIView):
    def post(self, request):
        events_data = request.data.get("events", [])
        if not isinstance(events_data, list) or not events_data:
            return Response({"error": "A non-empty 'events' list is required"}, status=status.HTTP_400_BAD_REQUEST)

        from api.models import BehaviorEvent

        objects = []
        errors = []
        for index, event in enumerate(events_data):
            uid = event.get("user_id")
            pid = event.get("product_id")
            action = event.get("action")
            if not all([uid, pid, action]):
                errors.append(f"Event {index}: missing required fields")
                continue
            if action not in VALID_ACTIONS:
                errors.append(f"Event {index}: invalid action '{action}'")
                continue
            objects.append(
                BehaviorEvent(
                    user_id=int(uid),
                    product_id=int(pid),
                    action=action,
                    session_id=event.get("session_id", ""),
                )
            )

        created = BehaviorEvent.objects.bulk_create(objects)
        return Response({"created": len(created), "errors": errors}, status=status.HTTP_201_CREATED)


class PopularRecommendationsView(APIView):
    def get(self, request):
        limit = int(request.GET.get("limit", 8))
        graph_client = Neo4jRecommender(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        try:
            books = graph_client.get_popular_books(limit=limit)
        except Exception:
            books = []
        finally:
            graph_client.close()

        if not books:
            books = _load_seed_books()
        return Response(_normalize_book_payload(books, limit), status=status.HTTP_200_OK)


class SuggestRecommendationsView(APIView):
    def get(self, request):
        limit = int(request.GET.get("limit", 8))
        return Response(_normalize_book_payload(_load_seed_books(), limit), status=status.HTTP_200_OK)


class ByCategoryRecommendationsView(APIView):
    def get(self, request):
        raw_book_id = request.GET.get("book_id")
        if not raw_book_id or not str(raw_book_id).isdigit():
            return Response({"error": "book_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        book_id = int(raw_book_id)
        graph_client = Neo4jRecommender(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        try:
            books = graph_client.recommend_related_products(book_id=book_id, limit=8)
        except Exception:
            books = []
        finally:
            graph_client.close()

        if not books:
            seed_books = _load_seed_books()
            target = next((book for book in seed_books if int(book.get("id")) == book_id), None)
            if not target:
                return Response([], status=status.HTTP_200_OK)
            category_name = target.get("category_name")
            books = [
                book for book in seed_books
                if book.get("category_name") == category_name and int(book.get("id")) != book_id
            ]

        return Response(_normalize_book_payload(books, 8), status=status.HTTP_200_OK)


class SessionRecommendationsView(APIView):
    def post(self, request):
        viewed = request.data.get("viewed_book_ids") or []
        if not isinstance(viewed, list) or not viewed:
            return Response([], status=status.HTTP_200_OK)

        viewed_ids = [int(item) for item in viewed if str(item).isdigit()]

        graph_client = Neo4jRecommender(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        try:
            books = graph_client.recommend_for_session(viewed_book_ids=viewed_ids, limit=8)
        except Exception:
            books = []
        finally:
            graph_client.close()

        if not books:
            seed_books = _load_seed_books()
            book_map = {int(book["id"]): book for book in seed_books if "id" in book}
            categories = {
                book_map[book_id].get("category_name")
                for book_id in viewed_ids
                if book_id in book_map and book_map[book_id].get("category_name")
            }
            books = [
                book for book in seed_books
                if int(book.get("id")) not in viewed_ids and book.get("category_name") in categories
            ] or seed_books

        return Response(_normalize_book_payload(books, 8), status=status.HTTP_200_OK)


class ChatRecommendationsView(APIView):
    def post(self, request):
        return ChatView().post(request)
