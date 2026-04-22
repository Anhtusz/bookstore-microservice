import os
import json
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi
import numpy as np

class RAGRetriever:
    def __init__(self, data_dir, model_name='all-MiniLM-L6-v2'):
        self.data_dir = data_dir
        self.chroma_client = chromadb.PersistentClient(path=os.path.join(data_dir, 'chroma_db'))
        self.collection = self.chroma_client.get_or_create_collection(name="books_collection")
        self.encoder = SentenceTransformer(model_name)
        
        self.books = []
        self.bm25 = None
        self.corpus_tokens = []
        
        self.load_data()
        
    def load_data(self):
        books_path = os.path.join(self.data_dir, 'books.json')
        if not os.path.exists(books_path):
            print("Books data not found. Please run data generator.")
            return
            
        with open(books_path, 'r', encoding='utf-8') as f:
            self.books = json.load(f)
            
        if self.collection.count() == 0:
            print("Indexing documents into ChromaDB...")
            documents = []
            metadatas = []
            ids = []
            
            for book in self.books:
                doc_text = f"Title: {book['title']}. Author: {book['author']}. Category: {book['category_name']}. Description: {book['description']}"
                documents.append(doc_text)
                metadatas.append({"id": book['id'], "title": book['title'], "category": book['category_name']})
                ids.append(str(book['id']))
                
            # Generate embeddings
            embeddings = self.encoder.encode(documents).tolist()
            
            # Add to Chroma
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print("Indexing complete.")
            
        # Initialize BM25
        print("Initializing BM25 index...")
        for book in self.books:
            doc_text = f"{book['title']} {book['author']} {book['category_name']} {book['description']}"
            self.corpus_tokens.append(doc_text.lower().split())
            
        self.bm25 = BM25Okapi(self.corpus_tokens)
        print("BM25 ready.")
        
    def semantic_search(self, query, top_k=5):
        query_embedding = self.encoder.encode([query]).tolist()
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
        return results
        
    def hybrid_search(self, query, top_k=5, alpha=0.5):
        # Semantic scores
        query_embedding = self.encoder.encode([query]).tolist()
        
        # We need to query more items to combine ranks
        semantic_results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=len(self.books)
        )
        
        semantic_ids = semantic_results['ids'][0]
        semantic_distances = semantic_results['distances'][0]
        
        # Normalize semantic scores (distances are usually L2 or Cosine, lower is better. Convert to score)
        max_dist = max(semantic_distances) if semantic_distances else 1
        semantic_scores = {sid: 1.0 - (dist / max_dist) for sid, dist in zip(semantic_ids, semantic_distances)}
        
        # BM25 scores
        tokenized_query = query.lower().split()
        bm25_scores_raw = self.bm25.get_scores(tokenized_query)
        max_bm25 = max(bm25_scores_raw) if max(bm25_scores_raw) > 0 else 1
        
        hybrid_scores = []
        for i, book in enumerate(self.books):
            book_id_str = str(book['id'])
            sem_score = semantic_scores.get(book_id_str, 0.0)
            bm25_score = bm25_scores_raw[i] / max_bm25
            
            final_score = alpha * sem_score + (1 - alpha) * bm25_score
            hybrid_scores.append((final_score, book))
            
        # Sort by final score
        hybrid_scores.sort(key=lambda x: x[0], reverse=True)
        
        # Return top K books
        return [item[1] for item in hybrid_scores[:top_k]]

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    
    retriever = RAGRetriever(data_dir)
    print("\nTesting Hybrid Search for 'science fiction space':")
    results = retriever.hybrid_search("science fiction space", top_k=3)
    for r in results:
        print(f"- {r['title']} ({r['category_name']})")
