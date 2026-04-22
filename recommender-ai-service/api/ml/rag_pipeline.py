import os
import requests
import chromadb
from sentence_transformers import SentenceTransformer, CrossEncoder
import google.generativeai as genai
from rank_bm25 import BM25Okapi

class AdvancedRAG:
    def __init__(self):
        print("Initializing RAG Pipeline Components...")
        # 1. Vector DB setup
        self.chroma_client = chromadb.EphemeralClient()
        self.collection = self.chroma_client.get_or_create_collection(name="bookstore_knowledge")
        
        self.embedder = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
        # 3. Cross-Encoder (Reranking)
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        
        # 4. LLM GenAI setup (ensure GEMINI_API_KEY is available)
        api_key = os.environ.get("GEMINI_API_KEY", "dummy_key")
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
        
        self.corpus_docs = []
        self.bm25 = None
        
        self.ingest_books_knowledge()
        
    def ingest_books_knowledge(self):
        """Fetch books and categories to populate the knowledge base dynamically."""
        docs = [
            "Cửa hàng chúng tôi miễn phí vận chuyển cho đơn hàng trên 50K.",
            "Chính sách đổi trả: Bạn có thể đổi sách trong vòng 30 ngày nếu còn nguyên vẹn."
        ]
        try:
            # 1. Fetch Categories
            cat_res = requests.get("http://catalog-service:8000/api/categories/", timeout=5)
            categories = {c["id"]: c["name"] for c in cat_res.json()} if cat_res.status_code == 200 else {}
            
            # 2. Fetch Catalog Items for Category Mapping
            item_res = requests.get("http://catalog-service:8000/api/items/", timeout=5)
            items = item_res.json() if item_res.status_code == 200 else []
            book_cat_map = {item["book_id"]: categories.get(item["category"], "Unknown") for item in items}
            
            # 3. Fetch Books
            book_res = requests.get("http://book-service:8000/api/books/", timeout=5)
            if book_res.status_code == 200:
                books = book_res.json()
                for b in books:
                    title = b.get('title', 'Unknown')
                    author = b.get('author', 'Unknown')
                    desc = b.get('description', '')
                    price = b.get('price', '0')
                    stock = b.get('stock', 0)
                    cat_name = book_cat_map.get(b.get('id'), "Không xác định")
                    
                    stock_status = f"còn hàng ({stock} quyển)" if stock > 0 else "đã hết hàng"
                    
                    doc = (f"Sách '{title}' của tác giả {author}. Thể loại: {cat_name}. "
                           f"Giá: {price}$. Mổ tả: {desc}. Tình trạng: {stock_status}.")
                    docs.append(doc)
            print(f"Began ingesting {len(docs)} documents into Knowledge Base!")
        except Exception as e:
            print(f"Error fetching dynamic database elements using RAG: {e}")
            
        self.add_documents(docs)

    def add_documents(self, documents):
        self.corpus_docs.extend(documents)
        # Tokenize BM25 corpus 
        tokenized_corpus = [doc.lower().split(" ") for doc in self.corpus_docs]
        self.bm25 = BM25Okapi(tokenized_corpus)
        
        # Insert ChromaDB
        embeddings = self.embedder.encode(documents).tolist()
        ids = [f"doc_{i}" for i in range(len(self.corpus_docs) - len(documents), len(self.corpus_docs))]
        self.collection.add(embeddings=embeddings, documents=documents, ids=ids)
        
    def hybrid_retrieval(self, query, top_k=5):
        if not self.corpus_docs:
            return []
            
        # BM25 Retrieval
        tokenized_query = query.lower().split(" ")
        bm25_scores = self.bm25.get_scores(tokenized_query)
        bm25_top_n = sorted(range(len(bm25_scores)), key=lambda i: bm25_scores[i], reverse=True)[:top_k]
        bm25_docs = [self.corpus_docs[i] for i in bm25_top_n]
        
        # ChromaDB Retrieve
        query_embedding = self.embedder.encode([query]).tolist()
        vector_results = self.collection.query(query_embeddings=query_embedding, n_results=top_k)
        vector_docs = vector_results['documents'][0] if vector_results['documents'] else []
        
        # Combine (Simple Set Union for speed)
        unique_docs = list(set(bm25_docs + vector_docs))
        return unique_docs
        
    def rerank(self, query, documents, top_k=3):
        if not documents:
            return []
        
        pairs = [[query, doc] for doc in documents]
        scores = self.cross_encoder.predict(pairs)
        
        doc_score_pairs = list(zip(documents, scores))
        doc_score_pairs.sort(key=lambda x: x[1], reverse=True)
        
        return [doc for doc, score in doc_score_pairs[:top_k]]
        
    def generate_answer(self, query):
        try:
            # 1. Hybrid Retrieval
            retrieved_docs = self.hybrid_retrieval(query, top_k=5)
            
            # 2. Reranking
            reranked_docs = self.rerank(query, retrieved_docs, top_k=3)
            
            # 3. Generation
            context = "\n".join([f"- {doc}" for doc in reranked_docs])
            prompt = (
                f"You are a helpful bookstore chatbot.\n\n"
                f"Context Information:\n{context}\n\n"
                f"User Query: {query}\n\n"
                f"Answer the user query based ONLY on the context. If you don't know, say you don't know."
            )
            response = self.gemini_model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Lỗi hệ thống khi gọi Gemini: {str(e)}"

# We instantiate globally so models are loaded only once a worker starts
rag_pipeline = AdvancedRAG()
