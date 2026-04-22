import os
import google.generativeai as genai

class RAGGenerator:
    def __init__(self, api_key=None):
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY", "")
        
        genai.configure(api_key=api_key)
        
        self.api_key = api_key
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
    def generate_recommendation_response(self, user_query, retrieved_books, graph_context=None, predicted_action=None):
        """
        Generate a response explaining recommendations based on multiple contexts.
        """
        prompt = f"User Query: {user_query}\n\n"
        
        prompt += "Retrieved Books Context:\n"
        for i, book in enumerate(retrieved_books):
            prompt += f"{i+1}. Title: {book.get('title', 'N/A')}, Category: {book.get('category_name', 'N/A')}, Desc: {book.get('description', 'N/A')}\n"
            
        if graph_context:
            prompt += f"\nGraph Context (Collaborative Filtering / History):\n{graph_context}\n"
            
        if predicted_action:
            prompt += f"\nPredicted User Action (Deep Learning Model): {predicted_action}\n"
            
        prompt += """
        Based on the user's query and the provided contexts, please provide:
        1. A brief explanation of why these books are recommended.
        2. A formatted list of the recommended books highlighting why each might be a good fit.
        Keep the response engaging and helpful for a bookstore customer.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"
            
    def chat(self, message):
        """General chat function for the bot"""
        try:
            response = self.model.generate_content(message)
            return response.text
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def graph_rag_chat(self, query, graph_contexts, semantic_contexts=None):
        graph_contexts = graph_contexts or []
        semantic_contexts = semantic_contexts or []

        if not graph_contexts:
            return {
                "answer": "I don't know based on the available context.",
                "sources": [],
                "used_context": [],
            }

        graph_lines = [f"- {item['text']}" for item in graph_contexts]
        semantic_lines = []
        for item in semantic_contexts:
            if isinstance(item, dict):
                title = item.get("title", "Unknown")
                category = item.get("category_name", "Unknown")
                semantic_lines.append(f"- Semantic candidate: {title} ({category})")
            else:
                semantic_lines.append(f"- Semantic candidate: {item}")

        prompt = (
            "You are a bookstore assistant using retrieval-augmented generation.\n"
            "Answer ONLY with facts explicitly supported by the supplied graph context.\n"
            "Graph context is the primary source of truth.\n"
            "Use semantic candidates only when they agree with the graph context.\n"
            "If the context is insufficient, reply exactly: \"I don't know based on the available context.\".\n"
            "Do not invent books, categories, reviews, prices, stock, or user behavior.\n\n"
            f"Graph Context:\n{os.linesep.join(graph_lines)}\n\n"
            f"Semantic Context:\n{os.linesep.join(semantic_lines) if semantic_lines else '- None'}\n\n"
            f"User Query: {query}\n\n"
            "Answer:"
        )

        try:
            response = self.model.generate_content(prompt)
            text = (response.text or "").strip() or "I don't know based on the available context."
        except Exception:
            text = "I don't know based on the available context."

        if text == "I don't know based on the available context.":
            books = [item for item in graph_contexts if item.get("kind") == "book"]
            if books:
                text = "Based on the knowledge graph, you can look at: " + "; ".join(
                    f"{book.get('title')} ({book.get('category_name')})"
                    for book in books[:3]
                ) + "."

        return {
            "answer": text,
            "sources": [],
            "used_context": [item["text"] for item in graph_contexts],
        }

if __name__ == "__main__":
    # Ensure GEMINI_API_KEY is set in environment for testing
    generator = RAGGenerator()
    
    mock_books = [
        {"title": "Dune", "category_name": "Science Fiction", "description": "Epic sci-fi on desert planet."},
        {"title": "The Martian", "category_name": "Science Fiction", "description": "Survival on Mars."}
    ]
    
    # print(generator.generate_recommendation_response("I love space adventures", mock_books, "User previously bought Foundation.", "purchase"))
