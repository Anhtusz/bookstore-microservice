import os
import google.generativeai as genai

class RAGGenerator:
    def __init__(self, api_key=None):
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY", "")
        
        genai.configure(api_key=api_key)
        
        # Use Gemini 1.5 Flash as requested (or a general available model)
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

if __name__ == "__main__":
    # Ensure GEMINI_API_KEY is set in environment for testing
    generator = RAGGenerator()
    
    mock_books = [
        {"title": "Dune", "category_name": "Science Fiction", "description": "Epic sci-fi on desert planet."},
        {"title": "The Martian", "category_name": "Science Fiction", "description": "Survival on Mars."}
    ]
    
    # print(generator.generate_recommendation_response("I love space adventures", mock_books, "User previously bought Foundation.", "purchase"))
