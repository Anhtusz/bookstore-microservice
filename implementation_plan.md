# Implementation Plan: Assignment B/C/D Fix

## Bước 2 — Lỗi chính đang chặn hệ thống

| # | Vấn đề | Impact |
|---|---|---|
| 1 | **Neo4j graph thiếu schema**: Không có node `Category`, `Review`. Thiếu relationships `BELONGS_TO`, `BOUGHT`, `REVIEWED`, `HAS_LABEL`. | Fail điểm B |
| 2 | **Không có label từ model_best**: Graph chưa lưu prediction label từ LSTM vào node User. | Fail điểm B |
| 3 | **ChatView không dùng RAG**: Gọi `generator.chat(message)` trực tiếp — raw LLM, không retrieval từ KB_Graph. | Fail điểm C |
| 4 | **Frontend Chatbot gọi sai URL**: `POST /recommender-ai/recommendations/chat/` → backend chỉ có `/recommender-ai/chat/`. | 404 mỗi lần chat |
| 5 | **Frontend gọi thiếu endpoints**: `GET /recommender-ai/recommendations/for_session/` và `GET /recommender-ai/recommendations/popular/` không tồn tại. | Recommendations không load |
| 6 | **Chatbot nhận `query` nhưng backend expect `message`**: payload mismatch. | Chat trả lỗi 400 |
| 7 | **`ChatView` trả `response` nhưng frontend expect `answer`**: response key mismatch. | Chat hiện `undefined` |

---

## Proposed Changes

### A. Backend — `recommender-ai-service`

#### [MODIFY] [graph/neo4j_client.py](file:///e:/QuePrj/bookstore-microservice/recommender-ai-service/graph/neo4j_client.py)

Viết lại `Neo4jRecommender` với:
- **Schema đầy đủ**: Node `User`, `Book`, `Category`, `Review`
- **Relationships**: `BELONGS_TO` (Book→Category), `BOUGHT` (User→Book), `REVIEWED` (User→Book), `VIEWED` (User→Book), `HAS_LABEL` (User→predicted_label string)
- **Constraints/Index**: `MERGE` thay `CREATE` để tránh duplicate
- **`apply_model_labels()`**: Load `model_best.pt`, predict label cho từng user từ lịch sử hành vi (action sequence), gắn vào graph qua `HAS_LABEL`
- **`get_graph_context_for_chat(query)`**: Query Neo4j để lấy context liên quan đến query (books, categories, reviews)

#### [NEW] `api/management/commands/build_graph.py`

Management command để build toàn bộ graph từ:
- `data/books.json` → Book + Category nodes
- `data/users.json` → User nodes  
- `data/data_user500.csv` → relationships (VIEWED, BOUGHT, REVIEWED)
- `model_best.pt` → HAS_LABEL relationships cho User

```bash
docker compose exec recommender-ai-service python manage.py build_graph
docker compose exec recommender-ai-service python manage.py build_graph --full  # clear + rebuild
```

---

#### [MODIFY] [rag/generator.py](file:///e:/QuePrj/bookstore-microservice/recommender-ai-service/rag/generator.py)

Thêm method `graph_rag_chat(query, graph_context, semantic_context)`:
- Nhận context từ KB_Graph (bắt buộc)
- Nhận context từ semantic retriever (tùy chọn)  
- Prompt **grounding**: ép model trả lời CHỈ dựa trên context, nếu không đủ context thì nói "I don't have information about that"
- Trả về `{"answer": ..., "sources": [...]}`

---

#### [MODIFY] [api/views.py](file:///e:/QuePrj/bookstore-microservice/recommender-ai-service/api/views.py)

**Fix ChatView** — thay raw LLM bằng RAG pipeline:
```
POST /api/chat/
{query} → Neo4j graph context retrieval + semantic retrieval → grounded LLM → {answer, sources}
```

**Add `ForSessionView`** — session-based recommendations:
```
POST /api/recommendations/for_session/
{viewed_book_ids} → Neo4j collaborative filter → return books
```

**Add `PopularView`** — popular books:
```
GET /api/recommendations/popular/?limit=8
→ books sorted by BOUGHT count in graph (fallback to books.json)
```

---

#### [MODIFY] [api/urls.py](file:///e:/QuePrj/bookstore-microservice/recommender-ai-service/api/urls.py)

Thêm routes mới:
```python
path('recommendations/chat/', ChatView),       # alias cho frontend
path('recommendations/for_session/', ForSessionView),
path('recommendations/popular/', PopularView),
```

---

### B. Frontend

#### [MODIFY] [Chatbot.jsx](file:///e:/QuePrj/bookstore-microservice/frontend/src/components/Chatbot.jsx)

Fixes:
- URL: `POST /recommender-ai/recommendations/chat/` ✓ (đã có, chỉ cần giữ)
- Payload: đổi `{ query }` → `{ query }` ✓ (backend sẽ accept `query`)
- Response: đọc `res.data.answer` ✓ (đã đúng, backend sẽ trả `answer`)
- Thêm hiển thị `sources` (list books trích dẫn từ graph) bên dưới câu trả lời

#### [MODIFY] [StorefrontPage.jsx](file:///e:/QuePrj/bookstore-microservice/frontend/src/pages/StorefrontPage.jsx)

- Không thay đổi gì — URL `/recommendations/for_session/` và `/recommendations/popular/` sẽ được tạo ở backend

---

## Verification Plan

```bash
# Build graph
docker compose exec recommender-ai-service python manage.py build_graph

# Test chat RAG
curl -X POST http://localhost:8000/api/recommender-ai/recommendations/chat/ \
  -H "Content-Type: application/json" \
  -d '{"query": "recommend a science fiction book"}'

# Test popular
curl http://localhost:8000/api/recommender-ai/recommendations/popular/?limit=5

# Test for_session  
curl -X POST http://localhost:8000/api/recommender-ai/recommendations/for_session/ \
  -H "Content-Type: application/json" \
  -d '{"viewed_book_ids": [1, 5, 10]}'
```

> [!IMPORTANT]
> **Không file generated data nào bị sửa.** Toàn bộ logic mới đọc từ file sẵn có.

> [!NOTE]
> **Thứ tự thực hiện**: graph/neo4j_client.py → management command build_graph → rag/generator.py → api/views.py → api/urls.py → Frontend → Verify
