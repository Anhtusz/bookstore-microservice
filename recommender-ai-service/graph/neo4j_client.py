import json
import os
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import torch
from neo4j import GraphDatabase

from models.sequence_models import BehaviorBiLSTM, BehaviorLSTM, BehaviorRNN


class Neo4jRecommender:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def ensure_constraints(self):
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT user_id_unique IF NOT EXISTS FOR (u:User) REQUIRE u.id IS UNIQUE")
            session.run("CREATE CONSTRAINT book_id_unique IF NOT EXISTS FOR (b:Book) REQUIRE b.id IS UNIQUE")
            session.run("CREATE CONSTRAINT category_name_unique IF NOT EXISTS FOR (c:Category) REQUIRE c.name IS UNIQUE")
            session.run("CREATE CONSTRAINT review_id_unique IF NOT EXISTS FOR (r:Review) REQUIRE r.id IS UNIQUE")
            session.run("CREATE CONSTRAINT label_name_unique IF NOT EXISTS FOR (l:Label) REQUIRE l.name IS UNIQUE")
            session.run("CREATE INDEX book_title_idx IF NOT EXISTS FOR (b:Book) ON (b.title)")
            session.run("CREATE INDEX book_author_idx IF NOT EXISTS FOR (b:Book) ON (b.author)")

    def clear_database(self):
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    def build_graph(
        self,
        csv_path: str,
        books_path: str,
        users_path: str,
        model_path: Optional[str] = None,
    ) -> Dict[str, int]:
        self.ensure_constraints()

        df = pd.read_csv(csv_path)
        books = self._load_json(books_path)
        users = self._load_json(users_path)

        with self.driver.session() as session:
            self._upsert_books_and_categories(session, books)
            self._upsert_users(session, users)
            self._upsert_behavior_graph(session, df)

        labels_created = self.apply_model_labels(csv_path=csv_path, model_path=model_path) if model_path else 0

        return {
            "users": len(users),
            "books": len(books),
            "categories": len({(book.get("category_name") or "Unknown").strip() for book in books}),
            "events": len(df),
            "labels": labels_created,
        }

    def sync_behavior_events(self, events: Iterable[Dict[str, Any]]):
        self.ensure_constraints()
        rows = list(events)
        if not rows:
            return
        df = pd.DataFrame(rows)
        with self.driver.session() as session:
            self._upsert_behavior_graph(session, df)

    def apply_model_labels(self, csv_path: str, model_path: str) -> int:
        if not model_path or not os.path.exists(model_path):
            return 0

        checkpoint = torch.load(model_path, map_location=torch.device("cpu"), weights_only=False)
        num_actions = checkpoint["num_actions"]
        model_name = checkpoint["model_name"]
        encoder_classes = [str(x) for x in checkpoint["encoder_classes"]]

        if model_name == "RNN":
            model = BehaviorRNN(num_actions)
        elif model_name == "LSTM":
            model = BehaviorLSTM(num_actions)
        else:
            model = BehaviorBiLSTM(num_actions)

        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        df = pd.read_csv(csv_path)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df = df.sort_values(["user_id", "timestamp"])

        action_to_idx = {action: idx for idx, action in enumerate(encoder_classes)}
        window_size = int(checkpoint.get("window_size", 10))
        rows = []

        for user_id, group in df.groupby("user_id"):
            sequence = [action_to_idx[action] for action in group["action"].tolist() if action in action_to_idx]
            if not sequence:
                continue
            sequence = sequence[-window_size:]
            seq_tensor = torch.tensor([sequence], dtype=torch.long)
            with torch.no_grad():
                logits = model(seq_tensor)
                predicted_idx = int(torch.argmax(logits, dim=1).item())
            label = encoder_classes[predicted_idx]
            rows.append({"user_id": int(user_id), "label": label})

        if not rows:
            return 0

        with self.driver.session() as session:
            session.run(
                """
                UNWIND $rows AS row
                MERGE (u:User {id: row.user_id})
                WITH u, row
                OPTIONAL MATCH (u)-[old:HAS_LABEL]->(:Label)
                DELETE old
                WITH u, row
                MERGE (l:Label {name: row.label})
                MERGE (u)-[:HAS_LABEL]->(l)
                """,
                rows=rows,
            )
        return len(rows)

    def get_user_behavior(self, user_id: int) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {id: $user_id})-[r]->(b:Book)
                RETURN type(r) AS action, b.id AS book_id, b.title AS book_title, coalesce(r.count, 1) AS count
                ORDER BY count DESC, book_title ASC
                """,
                user_id=int(user_id),
            )
            return [
                {
                    "action": record["action"],
                    "book_id": record["book_id"],
                    "book_title": record["book_title"],
                    "count": record["count"],
                }
                for record in result
            ]

    def recommend_related_products(self, book_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (seed:Book {id: $book_id})<-[:BOUGHT]-(u:User)-[:BOUGHT]->(rec:Book)
                WHERE rec.id <> $book_id
                OPTIONAL MATCH (rec)-[:BELONGS_TO]->(c:Category)
                RETURN rec.id AS id, rec.title AS title, rec.author AS author, rec.price AS price,
                       rec.image_url AS image_url, rec.stock AS stock, c.name AS category_name,
                       count(DISTINCT u) AS common_users
                ORDER BY common_users DESC, title ASC
                LIMIT $limit
                """,
                book_id=int(book_id),
                limit=int(limit),
            )
            return [dict(record) for record in result]

    def recommend_for_session(self, viewed_book_ids: List[int], limit: int = 8) -> List[Dict[str, Any]]:
        viewed_book_ids = [int(book_id) for book_id in viewed_book_ids]
        if not viewed_book_ids:
            return []

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (seed:Book)
                WHERE seed.id IN $viewed_ids
                WITH collect(seed) AS seeds
                UNWIND seeds AS seed
                OPTIONAL MATCH (seed)-[:BELONGS_TO]->(seedCat:Category)
                OPTIONAL MATCH (seed)<-[:BOUGHT|VIEWED|ADDED_TO_CART]-(u:User)-[:BOUGHT|VIEWED|ADDED_TO_CART]->(rec:Book)
                OPTIONAL MATCH (rec)-[:BELONGS_TO]->(recCat:Category)
                WHERE rec.id IS NOT NULL AND NOT rec.id IN $viewed_ids
                WITH rec, recCat, count(DISTINCT u) AS user_score,
                     count(DISTINCT CASE WHEN recCat = seedCat THEN seed END) AS category_score
                RETURN rec.id AS id, rec.title AS title, rec.author AS author, rec.price AS price,
                       rec.image_url AS image_url, rec.stock AS stock, rec.description AS description,
                       recCat.name AS category_name, (user_score * 2 + category_score) AS score
                ORDER BY score DESC, rec.title ASC
                LIMIT $limit
                """,
                viewed_ids=viewed_book_ids,
                limit=int(limit),
            )
            return [dict(record) for record in result]

    def get_popular_books(self, limit: int = 8) -> List[Dict[str, Any]]:
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (b:Book)
                OPTIONAL MATCH (:User)-[r:BOUGHT]->(b)
                OPTIONAL MATCH (b)-[:BELONGS_TO]->(c:Category)
                RETURN b.id AS id, b.title AS title, b.author AS author, b.price AS price,
                       b.image_url AS image_url, b.stock AS stock, b.description AS description,
                       c.name AS category_name, sum(coalesce(r.count, 0)) AS purchase_score
                ORDER BY purchase_score DESC, b.title ASC
                LIMIT $limit
                """,
                limit=int(limit),
            )
            return [dict(record) for record in result]

    def get_chat_context(
        self,
        query: str,
        user_id: Optional[int] = None,
        limit: int = 6,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        q = (query or "").strip().lower()
        if not q:
            return [], []
        q_terms = [term for term in q.replace(",", " ").split() if len(term) >= 3]

        contexts: List[Dict[str, Any]] = []
        sources: List[Dict[str, Any]] = []

        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (b:Book)-[:BELONGS_TO]->(c:Category)
                OPTIONAL MATCH (b)<-[purchase:BOUGHT]-(:User)
                OPTIONAL MATCH (review:Review)-[:ABOUT]->(b)
                WITH b, c, purchase, review,
                     CASE WHEN toLower(c.name) CONTAINS $q THEN 5 ELSE 0 END +
                     CASE WHEN toLower(b.title) CONTAINS $q THEN 4 ELSE 0 END +
                     CASE WHEN toLower(b.author) CONTAINS $q THEN 3 ELSE 0 END +
                     reduce(score = 0, term IN $q_terms |
                        score +
                        CASE WHEN toLower(c.name) CONTAINS term THEN 3 ELSE 0 END +
                        CASE WHEN toLower(b.title) CONTAINS term THEN 2 ELSE 0 END +
                        CASE WHEN toLower(b.author) CONTAINS term THEN 2 ELSE 0 END +
                        CASE WHEN toLower(coalesce(b.description, '')) CONTAINS term THEN 1 ELSE 0 END
                     ) AS relevance
                WHERE relevance > 0
                RETURN b.id AS id, b.title AS title, b.author AS author, c.name AS category_name,
                       b.description AS description, b.price AS price, b.stock AS stock,
                       relevance,
                       sum(coalesce(purchase.count, 0)) AS purchase_count,
                       count(DISTINCT review) AS review_count
                ORDER BY relevance DESC, purchase_count DESC, review_count DESC, b.title ASC
                LIMIT $limit
                """,
                q=q,
                q_terms=q_terms,
                limit=int(limit),
            )
            for record in result:
                payload = dict(record)
                payload["kind"] = "book"
                payload["text"] = (
                    f"Book #{payload['id']} '{payload['title']}' by {payload['author']} "
                    f"belongs to category {payload['category_name']}. "
                    f"Price: {payload.get('price')}. Stock: {payload.get('stock')}. "
                    f"Purchases in graph: {payload.get('purchase_count', 0)}. "
                    f"Reviews in graph: {payload.get('review_count', 0)}. "
                    f"Description: {payload.get('description') or 'N/A'}"
                )
                contexts.append(payload)
                sources.append({"type": "Book", "id": payload["id"], "title": payload["title"]})

            if user_id is not None:
                user_context = session.run(
                    """
                    MATCH (u:User {id: $user_id})
                    OPTIONAL MATCH (u)-[r:BOUGHT|VIEWED|ADDED_TO_CART|REVIEWED]->(b:Book)
                    OPTIONAL MATCH (u)-[:HAS_LABEL]->(l:Label)
                    RETURN collect(DISTINCT {
                        action: type(r),
                        book_id: b.id,
                        title: b.title,
                        category_name: head([(b)-[:BELONGS_TO]->(c:Category) | c.name])
                    }) AS behaviors,
                    collect(DISTINCT l.name) AS labels
                    """,
                    user_id=int(user_id),
                ).single()
                if user_context:
                    behaviors = [
                        item for item in (user_context["behaviors"] or [])
                        if item.get("action") and item.get("book_id") is not None
                    ]
                    labels = [label for label in (user_context["labels"] or []) if label]
                    if behaviors:
                        contexts.append(
                            {
                                "kind": "user_behavior",
                                "text": "User graph profile: " + "; ".join(
                                    f"{item['action']} book #{item['book_id']} '{item.get('title')}'"
                                    for item in behaviors[:8]
                                ),
                            }
                        )
                        sources.append({"type": "User", "id": int(user_id)})
                    if labels:
                        contexts.append({"kind": "label", "text": "Predicted user labels: " + ", ".join(labels)})
                        sources.append({"type": "Label", "names": labels})

            if len(contexts) < limit:
                review_result = session.run(
                    """
                    MATCH (u:User)-[:REVIEWED]->(r:Review)-[:ABOUT]->(b:Book)
                    OPTIONAL MATCH (b)-[:BELONGS_TO]->(c:Category)
                    WITH u, r, b, c,
                         CASE WHEN toLower(b.title) CONTAINS $q THEN 3 ELSE 0 END +
                         reduce(score = 0, term IN $q_terms |
                            score +
                            CASE WHEN toLower(b.title) CONTAINS term THEN 2 ELSE 0 END +
                            CASE WHEN toLower(coalesce(c.name, '')) CONTAINS term THEN 2 ELSE 0 END
                         ) AS relevance
                    WHERE relevance > 0
                    RETURN r.id AS id, u.id AS user_id, b.id AS book_id, b.title AS title,
                           c.name AS category_name, r.created_at AS created_at
                    ORDER BY relevance DESC, created_at DESC
                    LIMIT $limit
                    """,
                    q=q,
                    q_terms=q_terms,
                    limit=max(1, int(limit) - len(contexts)),
                )
                for record in review_result:
                    payload = dict(record)
                    contexts.append(
                        {
                            "kind": "review",
                            "text": (
                                f"Review node {payload['id']} created at {payload.get('created_at')} "
                                f"by user #{payload['user_id']} about book #{payload['book_id']} "
                                f"'{payload['title']}' in category {payload.get('category_name') or 'Unknown'}."
                            ),
                        }
                    )
                    sources.append({"type": "Review", "id": payload["id"], "book_id": payload["book_id"]})

        return contexts[:limit], sources[:limit]

    def _upsert_books_and_categories(self, session, books: List[Dict[str, Any]]):
        rows = []
        for book in books:
            category_name = (book.get("category_name") or "Unknown").strip() or "Unknown"
            rows.append(
                {
                    "id": int(book["id"]),
                    "title": book.get("title", ""),
                    "author": book.get("author", ""),
                    "description": book.get("description", ""),
                    "price": float(book.get("price", 0) or 0),
                    "stock": int(book.get("stock", 0) or 0),
                    "image_url": book.get("image_url", ""),
                    "category_name": category_name,
                }
            )

        session.run(
            """
            UNWIND $rows AS row
            MERGE (b:Book {id: row.id})
            SET b.title = row.title,
                b.author = row.author,
                b.description = row.description,
                b.price = row.price,
                b.stock = row.stock,
                b.image_url = row.image_url,
                b.category_name = row.category_name
            MERGE (c:Category {name: row.category_name})
            SET c.id = row.category_name
            MERGE (b)-[:BELONGS_TO]->(c)
            """,
            rows=rows,
        )

    def _upsert_users(self, session, users: List[Dict[str, Any]]):
        rows = []
        for user in users:
            rows.append(
                {
                    "id": int(user["id"]),
                    "name": user.get("name", ""),
                    "username": user.get("username", ""),
                    "email": user.get("email", ""),
                    "address": user.get("address", ""),
                }
            )
        session.run(
            """
            UNWIND $rows AS row
            MERGE (u:User {id: row.id})
            SET u.name = row.name,
                u.username = row.username,
                u.email = row.email,
                u.address = row.address
            """,
            rows=rows,
        )

    def _upsert_behavior_graph(self, session, df: pd.DataFrame):
        if df.empty:
            return

        normalized = df.copy()
        normalized["user_id"] = normalized["user_id"].astype(int)
        normalized["product_id"] = normalized["product_id"].astype(int)
        normalized["timestamp"] = normalized["timestamp"].astype(str)

        review_rows = []
        relation_rows: Dict[str, Dict[Tuple[int, int], Dict[str, Any]]] = defaultdict(dict)

        for row in normalized.to_dict("records"):
            user_id = int(row["user_id"])
            product_id = int(row["product_id"])
            timestamp = str(row.get("timestamp", ""))
            action = str(row.get("action", "")).lower()
            rel_type = self._map_action_to_rel(action)

            if rel_type == "REVIEWED":
                review_id = f"seed:{user_id}:{product_id}:{timestamp}"
                review_rows.append(
                    {
                        "review_id": review_id,
                        "user_id": user_id,
                        "product_id": product_id,
                        "created_at": timestamp,
                        "action": action,
                    }
                )
                relation_rows["REVIEWED_BOOK"][(user_id, product_id)] = {"user_id": user_id, "product_id": product_id}
                continue

            key = (user_id, product_id)
            bucket = relation_rows[rel_type]
            if key not in bucket:
                bucket[key] = {"user_id": user_id, "product_id": product_id, "count": 0, "last_seen": timestamp}
            bucket[key]["count"] += 1
            bucket[key]["last_seen"] = timestamp

        for rel_type, grouped in relation_rows.items():
            if not grouped:
                continue
            if rel_type == "REVIEWED_BOOK":
                session.run(
                    """
                    UNWIND $rows AS row
                    MERGE (u:User {id: row.user_id})
                    MERGE (b:Book {id: row.product_id})
                    MERGE (u)-[:REVIEWED]->(b)
                    """,
                    rows=list(grouped.values()),
                )
                continue

            session.run(
                f"""
                UNWIND $rows AS row
                MERGE (u:User {{id: row.user_id}})
                MERGE (b:Book {{id: row.product_id}})
                MERGE (u)-[r:{rel_type}]->(b)
                SET r.count = row.count,
                    r.last_seen = row.last_seen
                """,
                rows=list(grouped.values()),
            )

        if review_rows:
            session.run(
                """
                UNWIND $rows AS row
                MERGE (u:User {id: row.user_id})
                MERGE (b:Book {id: row.product_id})
                MERGE (r:Review {id: row.review_id})
                SET r.created_at = row.created_at,
                    r.action = row.action
                MERGE (u)-[:REVIEWED]->(r)
                MERGE (r)-[:ABOUT]->(b)
                MERGE (u)-[:REVIEWED]->(b)
                """,
                rows=review_rows,
            )

    def _map_action_to_rel(self, action: str) -> str:
        action = (action or "").lower()
        mapping = {
            "purchase": "BOUGHT",
            "review": "REVIEWED",
            "add_to_cart": "ADDED_TO_CART",
            "remove_cart": "REMOVED_FROM_CART",
            "view": "VIEWED",
            "click": "CLICKED",
            "search": "SEARCHED",
        }
        return mapping.get(action, "INTERACTED")

    @staticmethod
    def _load_json(path: str) -> List[Dict[str, Any]]:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
