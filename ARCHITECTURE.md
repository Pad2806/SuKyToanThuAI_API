# SuKyAI Backend — Microservices Architecture

## Cấu trúc thư mục

```
SuKyAI_API/
├── docker-compose.yml          ← Orchestrate toàn bộ 8 containers
├── infra/
│   └── init.sql                ← CREATE EXTENSION pgvector, pgcrypto...
│
├── shared/                     ← Thư viện dùng chung (không phải service)
│   └── core/
│       ├── database.py         ← Async SQLAlchemy engine
│       ├── settings.py         ← BaseServiceSettings
│       └── security.py         ← JWT verify, require_role(), ok(), err()
│
├── services/
│   ├── auth/                   ← 🔐 Auth Service (port 8001 internal)
│   │   ├── Dockerfile
│   │   └── app/
│   │       ├── main.py
│   │       ├── models/models.py     ← users, audit_log
│   │       ├── api/v1/auth.py       ← /auth/login, /refresh, /logout
│   │       ├── api/v1/users.py      ← /users (admin CRUD)
│   │       └── core/settings.py    ← SECRET_KEY, ALGORITHM...
│   │
│   ├── content/                ← 📜 Content Service (port 8002 internal)
│   │   ├── Dockerfile
│   │   └── app/
│   │       ├── main.py
│   │       ├── models/models.py     ← eras, grades, topics, lessons, events + junctions
│   │       ├── api/v1/eras.py
│   │       ├── api/v1/grades.py
│   │       ├── api/v1/lessons.py
│   │       ├── api/v1/topics.py
│   │       ├── api/v1/events.py     ← GET /events/:slug → calls story-service internally
│   │       └── core/settings.py    ← STORY_SERVICE_URL
│   │
│   ├── rag/                    ← 🧠 RAG Service (port 8003 internal)
│   │   ├── Dockerfile
│   │   └── app/
│   │       ├── main.py
│   │       ├── models/models.py     ← source_documents, event_sources, chunks, embeddings
│   │       ├── parsers/
│   │       │   └── document_parser.py  ← TXT / MD / PDF parser (pymupdf)
│   │       ├── api/v1/documents.py  ← POST /documents (upload PDF/TXT/MD)
│   │       ├── api/v1/event_sources.py
│   │       ├── api/v1/search.py
│   │       └── core/settings.py    ← EMBED_MODEL, S3_*
│   │
│   ├── story/                  ← 📖 Story Service (port 8004 internal)
│   │   ├── Dockerfile
│   │   └── app/
│   │       ├── main.py
│   │       ├── models/models.py     ← event_story_versions, block_citations, image_assets, review_items
│   │       ├── api/v1/story_versions.py
│   │       ├── api/v1/images.py
│   │       ├── api/v1/review.py
│   │       └── core/settings.py
│   │
│   └── ai-worker/              ← ⚙️ AI Worker (background, no HTTP exposure)
│       ├── Dockerfile
│       └── app/
│           ├── worker.py           ← Entry: python -m app.worker
│           ├── models/models.py    ← generation_jobs
│           ├── handlers/
│           │   ├── ingest_handler.py    ← parse → chunk → embed
│           │   ├── story_handler.py     ← RAG retrieve → LLM generate → save
│           │   └── image_handler.py     ← AI image gen → S3 → review
│           └── core/settings.py    ← NINEROUTER_API_KEY, *_SERVICE_URL
│
└── alembic/                    ← Single migration set (runs against shared DB)
    └── versions/               ← 13 migrations hiện có + migration mới
```

## Docker Services Map

| Container | Build from | Port nội bộ | Route qua Gateway |
|---|---|---|---|
| `sukyai-db` | `pgvector/pgvector:pg16` | 5432 | — |
| `sukyai-minio` | `minio/minio` | 9000, 9001 | — |
| `sukyai-gateway` | `traefik:v2.10` | 80, 8080 | — |
| `sukyai-auth` | `services/auth` | 8000 | `/api/v1/auth`, `/api/v1/users` |
| `sukyai-content` | `services/content` | 8000 | `/api/v1/eras`, `/api/v1/grades`, `/api/v1/events`... |
| `sukyai-rag` | `services/rag` | 8000 | `/api/v1/documents`, `/api/v1/search` |
| `sukyai-story` | `services/story` | 8000 | `/api/v1/story`, `/api/v1/images`, `/api/v1/review-items` |
| `sukyai-ai-worker` | `services/ai-worker` | — | Không expose |

## Quy tắc giao tiếp giữa services

1. **Frontend → Gateway → Service**: Mọi request từ ngoài đi qua Traefik
2. **Service A → Service B**: Gọi HTTP nội bộ qua tên container (ví dụ: `http://sukyai-story:8000/internal/...`)
3. **Cấm**: Service A KHÔNG được `JOIN` bảng DB của Service B — mọi dữ liệu cross-service phải qua HTTP call
4. **DB sở hữu**: Mỗi service chỉ `INSERT/UPDATE/DELETE` bảng của mình

## Ví dụ: GET /api/v1/events/chien-thang-bach-dang-938

```
Frontend → Traefik → sukyai-content:8000/api/v1/events/chien-thang-bach-dang-938
    ↓
content-service: SELECT * FROM events WHERE slug = '...'
    ↓
content-service: GET http://sukyai-story:8000/internal/events/{event_id}/published-story
    ↓
story-service: SELECT story_json FROM event_story_versions WHERE event_id = ... AND status = 'published'
    ↓
story-service → content-service → Traefik → Frontend
```

## Ví dụ: Ingest PDF cả quyển SGK Lớp 6

```
Admin → Traefik → sukyai-rag:8000/api/v1/documents (multipart PDF)
    ↓
rag-service: validate + upload → MinIO
    ↓
rag-service: INSERT generation_jobs (type='ingest') → DB
    ↓
sukyai-ai-worker: poll generation_jobs → dequeue
    ↓
ai-worker: GET file từ MinIO → PdfParser.extract() → text
    ↓
ai-worker: GPT-4o-mini detect lesson boundaries → split thành chunks theo bài
    ↓
ai-worker: Embed mỗi chunk → chunk_embeddings (pgvector)
    ↓
ai-worker: POST http://sukyai-rag:8000/internal/chunks (bulk insert)
    ↓
ai-worker: UPDATE generation_jobs status='succeeded'
```

## Bước tiếp theo (TODO)

- [ ] Implement `services/auth/app/api/v1/auth.py` (login/JWT)
- [ ] Implement `services/content/app/api/v1/events.py` (CRUD + search)
- [ ] Implement `services/rag/app/api/v1/documents.py` (upload + ingest)
- [ ] Implement `services/ai-worker/app/worker.py` (job polling loop)
- [ ] Implement `services/ai-worker/app/handlers/ingest_handler.py` (PDF → chunks)
- [ ] Thêm migration `014_add_pdf_support.py` (mở rộng mime_type CHECK)
- [ ] Viết `requirements.txt` cho từng service
