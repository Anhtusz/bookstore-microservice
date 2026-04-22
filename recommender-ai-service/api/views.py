import os
import torch
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import json

from rag.retriever import RAGRetriever
from rag.generator import RAGGenerator
from graph.neo4j_client import Neo4jRecommender
from models.sequence_models import BehaviorRNN, BehaviorLSTM, BehaviorBiLSTM

base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_dir = os.path.join(base_dir, 'data')

# Initialize RAG components globally (lazy loading ideally, but okay for prototype)
try:
    retriever = RAGRetriever(data_dir)
    generator = RAGGenerator()
except Exception as e:
    print(f"Warning: Failed to initialize RAG components: {e}")
    retriever = None
    generator = None

# Neo4j setup
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://db-neo4j:7687")
NEO4J_USER = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", "password")

# ML Model setup
model_path = os.path.join(base_dir, 'models', 'model_best.pt')
ml_model = None
action_encoder_classes = []

try:
    if os.path.exists(model_path):
        checkpoint = torch.load(model_path, map_location=torch.device('cpu'))
        num_actions = checkpoint['num_actions']
        model_name = checkpoint['model_name']
        action_encoder_classes = checkpoint['encoder_classes']
        
        if model_name == 'RNN':
            ml_model = BehaviorRNN(num_actions)
        elif model_name == 'LSTM':
            ml_model = BehaviorLSTM(num_actions)
        else:
            ml_model = BehaviorBiLSTM(num_actions)
            
        ml_model.load_state_dict(checkpoint['model_state_dict'])
        ml_model.eval()
except Exception as e:
    print(f"Warning: Failed to load ML model: {e}")

class RecommendView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        query = request.data.get('query', '')
        
        if not user_id:
            return Response({"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            # 1. Get graph context
            graph_client = Neo4jRecommender(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
            behavior = graph_client.get_user_behavior(user_id)
            graph_client.close()
            
            graph_context = f"User {user_id} has interacted with these books: {behavior}" if behavior else "No prior history."
            
            # 2. Retrieve books via RAG
            # If no query provided, just recommend generally based on random categories
            search_query = query if query else "popular books recommendations"
            retrieved_books = retriever.hybrid_search(search_query, top_k=5) if retriever else []
            
            # 3. Generate explanation
            if generator:
                explanation = generator.generate_recommendation_response(
                    user_query=search_query,
                    retrieved_books=retrieved_books,
                    graph_context=graph_context
                )
            else:
                explanation = "Generative AI is currently unavailable."
                
            return Response({
                "recommended_books": retrieved_books,
                "explanation": explanation
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChatView(APIView):
    def post(self, request):
        # Graph-RAG chat: MUST retrieve from Neo4j and ground answer.
        query = request.data.get('query') or request.data.get('message')
        user_id = request.data.get('user_id')

        if not query:
            return Response({"error": "query is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            graph_client = Neo4jRecommender(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
            contexts, sources = graph_client.get_chat_context(query=query, user_id=int(user_id) if user_id else None, limit=6)
            graph_client.close()
        except Exception as e:
            contexts, sources = [], []

        # Enforce "I don't know" when no context.
        if not contexts:
            return Response(
                {
                    "answer": "I don't know based on the available knowledge graph context.",
                    "sources": [],
                    "context": [],
                },
                status=status.HTTP_200_OK,
            )

        context_text = "\n".join([f"- {c}" for c in contexts])
        prompt = (
            "You are a bookstore assistant.\n"
            "You MUST answer using ONLY the provided context.\n"
            "If the answer is not explicitly supported by the context, reply exactly: \"I don't know based on the available context.\".\n\n"
            f"Context:\n{context_text}\n\n"
            f"User query: {query}\n\n"
            "Answer:"
        )

        if not generator:
            # Minimal fallback without LLM: return context as answer.
            return Response(
                {"answer": "Here is what I found:\n" + context_text, "sources": sources, "context": contexts},
                status=status.HTTP_200_OK,
            )

        answer = generator.chat(prompt)
        return Response({"answer": answer, "sources": sources, "context": contexts}, status=status.HTTP_200_OK)

class PredictView(APIView):
    def post(self, request):
        sequence = request.data.get('sequence') # e.g. ["view", "click", "add_to_cart"]
        
        if not sequence or not isinstance(sequence, list):
            return Response({"error": "Valid sequence list is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        if not ml_model or len(action_encoder_classes) == 0:
            return Response({"error": "ML Model not trained/loaded"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        try:
            # Encode sequence
            encoded_seq = []
            for action in sequence:
                # Find index in classes
                if action in action_encoder_classes:
                    idx = list(action_encoder_classes).index(action)
                    encoded_seq.append(idx)
                else:
                    # Fallback to 0 if unknown
                    encoded_seq.append(0)
                    
            # Predict
            seq_tensor = torch.tensor([encoded_seq], dtype=torch.long)
            with torch.no_grad():
                outputs = ml_model(seq_tensor)
                _, predicted_idx = torch.max(outputs, 1)
                
            predicted_action = action_encoder_classes[predicted_idx.item()]

            # Optionally persist label into Neo4j for KB graph ("HAS_LABEL").
            try:
                uid = request.data.get('user_id')
                if uid is not None:
                    graph_client = Neo4jRecommender(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
                    graph_client.ensure_constraints()
                    with graph_client.driver.session() as session:
                        session.run(
                            """
                            MERGE (u:User {id: $uid})
                            MERGE (l:Label {name: $label})
                            MERGE (u)-[:HAS_LABEL]->(l)
                            """,
                            uid=int(uid),
                            label=str(predicted_action),
                        )
                    graph_client.close()
            except Exception:
                pass
            
            return Response({
                "sequence": sequence,
                "predicted_next_action": predicted_action
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


VALID_ACTIONS = {'view', 'click', 'add_to_cart', 'purchase', 'remove_cart', 'search', 'review'}


class TrackEventView(APIView):
    """Record a single user behavior event."""

    def post(self, request):
        user_id = request.data.get('user_id')
        product_id = request.data.get('product_id')
        action = request.data.get('action')

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
            session_id=request.data.get('session_id', ''),
        )

        return Response(
            {"id": event.id, "status": "tracked"},
            status=status.HTTP_201_CREATED,
        )


class TrackBatchView(APIView):
    """Record multiple user behavior events in a single request."""

    def post(self, request):
        events_data = request.data.get('events', [])

        if not isinstance(events_data, list) or len(events_data) == 0:
            return Response(
                {"error": "A non-empty 'events' list is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from api.models import BehaviorEvent

        objects = []
        errors = []
        for i, ev in enumerate(events_data):
            uid = ev.get('user_id')
            pid = ev.get('product_id')
            act = ev.get('action')
            if not all([uid, pid, act]):
                errors.append(f"Event {i}: missing required fields")
                continue
            if act not in VALID_ACTIONS:
                errors.append(f"Event {i}: invalid action '{act}'")
                continue
            objects.append(
                BehaviorEvent(
                    user_id=int(uid),
                    product_id=int(pid),
                    action=act,
                    session_id=ev.get('session_id', ''),
                )
            )

        created = BehaviorEvent.objects.bulk_create(objects)

        return Response(
            {"created": len(created), "errors": errors},
            status=status.HTTP_201_CREATED,
        )


def _load_seed_books(data_dir: str):
    books_path = os.path.join(data_dir, 'books.json')
    with open(books_path, 'r', encoding='utf-8') as f:
        return json.load(f)


class PopularRecommendationsView(APIView):
    """Return popular books (best-effort) for storefront ribbon."""

    def get(self, request):
        limit = int(request.GET.get('limit', 8))
        # Prefer Neo4j: rank by BOUGHT count.
        try:
            graph_client = Neo4jRecommender(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
            with graph_client.driver.session() as session:
                res = session.run(
                    """
                    MATCH (:User)-[r:BOUGHT]->(b:Book)
                    RETURN b.id AS id, b.title AS title, b.author AS author, sum(coalesce(r.count,1)) AS score
                    ORDER BY score DESC
                    LIMIT $limit
                    """,
                    limit=limit,
                )
                ids = [int(r["id"]) for r in res if r.get("id") is not None]
            graph_client.close()
        except Exception:
            ids = []

        books = _load_seed_books(data_dir)
        by_id = {int(b["id"]): b for b in books if "id" in b}
        if ids:
            out = [by_id[i] for i in ids if i in by_id]
        else:
            out = books[:limit]
        return Response(out[:limit], status=status.HTTP_200_OK)


class SuggestRecommendationsView(APIView):
    """Simple fallback suggestions (no user context)."""

    def get(self, request):
        limit = int(request.GET.get('limit', 8))
        books = _load_seed_books(data_dir)
        return Response(books[:limit], status=status.HTTP_200_OK)


class ByCategoryRecommendationsView(APIView):
    """Books in same category as given book_id."""

    def get(self, request):
        book_id = request.GET.get('book_id')
        if not book_id:
            return Response({"error": "book_id is required"}, status=status.HTTP_400_BAD_REQUEST)
        book_id = int(book_id)
        books = _load_seed_books(data_dir)
        target = next((b for b in books if int(b.get("id")) == book_id), None)
        if not target:
            return Response([], status=status.HTTP_200_OK)
        cat = target.get("category_name")
        out = [b for b in books if b.get("category_name") == cat and int(b.get("id")) != book_id]
        return Response(out[:8], status=status.HTTP_200_OK)


class SessionRecommendationsView(APIView):
    """Recommend based on recently viewed book ids."""

    def post(self, request):
        viewed = request.data.get('viewed_book_ids') or []
        if not isinstance(viewed, list) or len(viewed) == 0:
            return Response([], status=status.HTTP_200_OK)
        viewed_ids = [int(x) for x in viewed if str(x).isdigit()]

        books = _load_seed_books(data_dir)
        by_id = {int(b["id"]): b for b in books if "id" in b}
        cats = [by_id[i].get("category_name") for i in viewed_ids if i in by_id]
        cats = [c for c in cats if c]
        if not cats:
            return Response(books[:8], status=status.HTTP_200_OK)

        # Rank books by category overlap.
        cat_set = set(cats)
        out = [b for b in books if b.get("category_name") in cat_set and int(b.get("id")) not in viewed_ids]
        return Response(out[:8], status=status.HTTP_200_OK)


class ChatRecommendationsView(APIView):
    """Frontend-compatible wrapper: POST {query, user_id?} -> {answer,...}"""

    def post(self, request):
        # Delegate to ChatView logic for Graph-RAG.
        return ChatView().post(request)
