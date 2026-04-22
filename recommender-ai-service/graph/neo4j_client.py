import os
import json
import pandas as pd
from neo4j import GraphDatabase
from typing import Any, Dict, List, Optional, Tuple

class Neo4jRecommender:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def ensure_constraints(self):
        """Create minimal constraints/indexes to avoid duplicates and speed up lookups."""
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
            session.run("CREATE CONSTRAINT book_id_unique IF NOT EXISTS FOR (b:Book) REQUIRE b.id IS UNIQUE")
            session.run("CREATE CONSTRAINT category_id_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.id IS UNIQUE")
            session.run("CREATE CONSTRAINT review_id_unique IF NOT EXISTS FOR (r:Review) REQUIRE r.id IS UNIQUE")
            session.run("CREATE CONSTRAINT label_name_unique IF NOT EXISTS FOR (l:Label) REQUIRE l.name IS UNIQUE")

    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            print("Cleared Neo4j database.")

    def build_graph(self, csv_path, books_path, users_path):
        print("Building Knowledge Graph in Neo4j...")
        self.ensure_constraints()
        
        # Load data
        df = pd.read_csv(csv_path)
        with open(books_path, 'r', encoding='utf-8') as f:
            books = json.load(f)
        with open(users_path, 'r', encoding='utf-8') as f:
            users = json.load(f)

        with self.driver.session() as session:
            # Create Book Nodes
            print("Creating Book nodes...")
            for book in books:
                session.run(
                    "MERGE (b:Book {id: $id}) "
                    "SET b.title = $title, b.author = $author, b.category_name = $category_name, b.description = $description",
                    id=book['id'],
                    title=book.get('title', ''),
                    author=book.get('author', ''),
                    category_name=book.get('category_name', ''),
                    description=book.get('description', ''),
                )

                # Category Node + BELONGS_TO
                cat_name = book.get('category_name') or "Unknown"
                # Use deterministic category id via hash-like mapping isn't stable across runs.
                # Instead, derive from category name by storing as both id and name (id=name) for uniqueness.
                session.run(
                    "MERGE (c:Category {id: $cid}) SET c.name = $name "
                    "WITH c MATCH (b:Book {id: $bid}) "
                    "MERGE (b)-[:BELONGS_TO]->(c)",
                    cid=cat_name, name=cat_name, bid=book['id']
                )

            # Create User Nodes
            print("Creating User nodes...")
            for user in users:
                session.run(
                    "MERGE (u:User {id: $id}) "
                    "SET u.username = $username",
                    id=user['id'], username=user['username']
                )

            # Create Relationships based on behaviors
            print("Creating relationships...")
            records = df.to_dict('records')
            actions = df['action'].unique()
            for action in actions:
                action_records = [r for r in records if r['action'] == action]
                rel_type = self._map_action_to_rel(action)
                print(f"Creating {rel_type} relationships ({len(action_records)} records)...")
                
                if rel_type in ("REVIEWED",):
                    # REVIEWED creates a Review node too
                    query = """
                    UNWIND $batch AS record
                    MERGE (u:User {id: record.user_id})
                    MERGE (b:Book {id: record.product_id})
                    MERGE (r:Review {id: record.review_id})
                    SET r.action = record.action, r.created_at = record.timestamp
                    MERGE (u)-[:REVIEWED]->(r)
                    MERGE (r)-[:ABOUT]->(b)
                    """
                    batch = []
                    for r in action_records:
                        batch.append({
                            "user_id": int(r["user_id"]),
                            "product_id": int(r["product_id"]),
                            "action": r.get("action", "review"),
                            "timestamp": str(r.get("timestamp", "")),
                            "review_id": f"seed:{r.get('user_id')}:{r.get('product_id')}:{r.get('timestamp','')}",
                        })
                    session.run(query, batch=batch)
                else:
                    query = f"""
                    UNWIND $batch AS record
                    MERGE (u:User {{id: record.user_id}})
                    MERGE (b:Book {{id: record.product_id}})
                    MERGE (u)-[r:{rel_type}]->(b)
                    ON CREATE SET r.count = 1
                    ON MATCH SET r.count = r.count + 1
                    """
                    batch = [{"user_id": int(r["user_id"]), "product_id": int(r["product_id"])} for r in action_records]
                    session.run(query, batch=batch)
                
        print("Knowledge Graph build complete.")

    def _map_action_to_rel(self, action: str) -> str:
        action = (action or "").lower()
        if action == "purchase":
            return "BOUGHT"
        if action == "review":
            return "REVIEWED"
        if action == "add_to_cart":
            return "ADDED_TO_CART"
        if action == "remove_cart":
            return "REMOVED_FROM_CART"
        if action == "view":
            return "VIEWED"
        if action == "click":
            return "CLICKED"
        if action == "search":
            return "SEARCHED"
        return action.upper() or "INTERACTED"

    def get_user_behavior(self, user_id):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})-[r]->(b:Book)
                RETURN type(r) as action, b.id as book_id, b.title as book_title, coalesce(r.count, 1) as count
            """, user_id=user_id)
            return [{"action": record["action"], "book_id": record["book_id"], "book_title": record["book_title"], "count": record["count"]} for record in result]

    def recommend_related_products(self, book_id, limit=5):
        # Recommend based on Collaborative Filtering using Graph (Users who bought this also bought)
        with self.driver.session() as session:
            result = session.run("""
                MATCH (b:Book {id: $book_id})<-[:BOUGHT]-(u:User)-[:BOUGHT]->(rec:Book)
                WHERE rec.id <> $book_id
                RETURN rec.id as recommended_id, rec.title as title, count(u) as common_users
                ORDER BY common_users DESC
                LIMIT $limit
            """, book_id=book_id, limit=limit)
            return [{"id": record["recommended_id"], "title": record["title"], "common_users": record["common_users"]} for record in result]

    def get_chat_context(self, query: str, user_id: Optional[int] = None, limit: int = 6) -> Tuple[List[str], List[Dict[str, Any]]]:
        """Retrieve graph-grounded context snippets for Graph-RAG chat."""
        q = (query or "").strip()
        if not q:
            return [], []
        q_l = q.lower()
        with self.driver.session() as session:
            sources: List[Dict[str, Any]] = []
            contexts: List[str] = []

            # 1) Book matches by title/author/category
            res = session.run(
                """
                MATCH (b:Book)-[:BELONGS_TO]->(c:Category)
                WHERE toLower(b.title) CONTAINS $q OR toLower(b.author) CONTAINS $q OR toLower(c.name) CONTAINS $q
                RETURN b.id AS id, b.title AS title, b.author AS author, c.name AS category, b.description AS description
                LIMIT $limit
                """,
                q=q_l,
                limit=limit,
            )
            for r in res:
                contexts.append(
                    f"Book #{r['id']}: '{r['title']}' by {r['author']} (Category: {r['category']}). Description: {r.get('description') or ''}".strip()
                )
                sources.append({"type": "Book", "id": r["id"]})

            # 2) If user_id present: recent behavior + labels
            if user_id is not None:
                res2 = session.run(
                    """
                    MATCH (u:User {id: $uid})
                    OPTIONAL MATCH (u)-[r]->(b:Book)
                    WITH u, collect({rel:type(r), book_id:b.id, title:b.title, count: coalesce(r.count,1)}) AS rels
                    OPTIONAL MATCH (u)-[:HAS_LABEL]->(l:Label)
                    RETURN rels AS rels, collect(l.name) AS labels
                    """,
                    uid=int(user_id),
                ).single()
                if res2:
                    rels = [x for x in (res2["rels"] or []) if x.get("rel") and x.get("book_id")]
                    labels = res2["labels"] or []
                    if rels:
                        contexts.append("User behavior summary: " + "; ".join(
                            [f"{x['rel']}→Book#{x['book_id']}('{x.get('title','')}') x{int(x.get('count') or 1)}" for x in rels[:10]]
                        ))
                        sources.append({"type": "User", "id": int(user_id)})
                    if labels:
                        contexts.append("User labels: " + ", ".join(labels))
                        sources.append({"type": "Label", "name": labels})

            # 3) Reviews relevant to query (by book match)
            if len(contexts) < limit:
                res3 = session.run(
                    """
                    MATCH (r:Review)-[:ABOUT]->(b:Book)
                    WHERE toLower(b.title) CONTAINS $q
                    RETURN r.id AS rid, b.id AS bid, b.title AS title, r.created_at AS created_at
                    LIMIT $limit
                    """,
                    q=q_l,
                    limit=limit,
                )
                for r in res3:
                    contexts.append(f"Review {r['rid']} about Book #{r['bid']} '{r['title']}' (created_at: {r.get('created_at')}).")
                    sources.append({"type": "Review", "id": r["rid"]})

            return contexts[:limit], sources[:limit]

if __name__ == "__main__":
    # Test script locally
    # Assumes Neo4j is running locally on default ports with neo4j/password
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "password"
    
    client = Neo4jRecommender(URI, USER, PASSWORD)
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    csv_path = os.path.join(data_dir, 'data_user500.csv')
    books_path = os.path.join(data_dir, 'books.json')
    users_path = os.path.join(data_dir, 'users.json')
    
    try:
        client.clear_database()
        client.build_graph(csv_path, books_path, users_path)
        
        print("\nTest User Behavior (User 1):")
        print(client.get_user_behavior(1))
        
        print("\nTest Recommendations for Book 1:")
        print(client.recommend_related_products(1))
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        print("Make sure Neo4j is running in Docker and accessible at localhost:7687.")
    finally:
        client.close()
