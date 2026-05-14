# SuKyAI Backend — Hướng dẫn chi tiết các Service & Folder

---

## 📌 Tổng quan kiến trúc

```
Frontend (SuKyAI_Web)
        │
        ▼
 [sukyai-gateway]   ← Traefik — nhận toàn bộ request từ ngoài, route vào đúng service
        │
   ┌────┴─────────────────────────────────────┐
   │              Docker Network              │
   │  sukyai-auth  sukyai-content             │
   │  sukyai-rag   sukyai-story               │
   │  sukyai-ai-worker (background)           │
   └────────────────┬─────────────────────────┘
                    │
              [sukyai-db]          ← PostgreSQL 16 + pgvector
              [sukyai-minio]       ← Object Storage (PDF, images)
```

---

## 🔐 1. Auth Service (`services/auth/`)

### Nhiệm vụ
Quản lý xác thực và phân quyền. Đây là service duy nhất **cấp phát JWT**.
Các service khác chỉ **xác minh** JWT, không gọi Auth Service để verify.

### Bảng DB sở hữu
| Bảng | Mô tả |
|---|---|
| `users` | Tài khoản hệ thống (admin / editor / viewer) |
| `audit_log` | Lịch sử mọi thao tác quan trọng |

### Cấu trúc folder
```
services/auth/
├── Dockerfile
└── app/
    ├── main.py                  ← FastAPI app, đăng ký router
    ├── core/
    │   └── settings.py          ← SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_MINUTES
    ├── models/
    │   └── models.py            ← SQLAlchemy: User, AuditLog
    ├── schemas/
    │   └── auth.py              ← Pydantic: LoginInput, TokenResponse, UserOut
    ├── services/
    │   └── auth_service.py      ← Logic: verify_password, create_token, refresh_token
    └── api/v1/
        ├── auth.py              ← POST /auth/login, /auth/refresh, /auth/logout
        └── users.py             ← GET/POST/PATCH /users (admin only)
```

### API Endpoints
| Method | Path | Role |
|---|---|---|
| POST | `/api/v1/auth/login` | Public |
| POST | `/api/v1/auth/refresh` | Public |
| POST | `/api/v1/auth/logout` | Any |
| GET | `/api/v1/auth/me` | Any |
| GET | `/api/v1/users` | admin |
| POST | `/api/v1/users` | admin |
| PATCH | `/api/v1/users/:id` | admin |

---

## 📜 2. Content Service (`services/content/`)

### Nhiệm vụ
Quản lý toàn bộ **metadata** của nội dung lịch sử: thời kỳ, khối lớp,
bài học, chủ đề, và sự kiện. Đây là service Frontend gọi nhiều nhất.

Khi trả `EventDetail`, service này sẽ tự động gọi HTTP nội bộ tới
**Story Service** để lấy `story_json` của phiên bản đã publish.

### Bảng DB sở hữu
| Bảng | Mô tả |
|---|---|
| `eras` | Thời kỳ lịch sử (Bắc thuộc, Lý-Trần...) |
| `grades` | Khối lớp 5-12 |
| `lessons` | Bài học SGK (1:1 với sách giáo khoa) |
| `topics` | Chủ đề chéo (chống ngoại xâm, văn hoá...) |
| `events` | Sự kiện lịch sử (metadata, không chứa story) |
| `event_topics` | Junction: Event ↔ Topic |
| `event_grades` | Junction: Event ↔ Grade (tag mức độ) |
| `lesson_events` | Junction: Lesson ↔ Event (có thứ tự) |

### Cấu trúc folder
```
services/content/
├── Dockerfile
└── app/
    ├── main.py
    ├── core/
    │   └── settings.py          ← STORY_SERVICE_URL (để gọi nội bộ)
    ├── models/
    │   └── models.py            ← Era, Grade, Topic, Lesson, Event + junctions
    ├── schemas/
    │   ├── event.py             ← EventOut, EventCreateInput, EventPatchInput
    │   ├── era.py               ← EraOut, EraCreateInput
    │   ├── grade.py
    │   ├── lesson.py
    │   └── topic.py
    ├── services/
    │   ├── event_service.py     ← CRUD + search + normalize Vietnamese text
    │   ├── era_service.py
    │   └── story_client.py      ← HTTP client gọi story-service lấy story_json
    └── api/v1/
        ├── events.py            ← GET/POST/PATCH/DELETE /events
        ├── eras.py              ← GET/POST/PATCH /eras
        ├── grades.py            ← GET /grades, /grades/:slug/lessons
        ├── lessons.py           ← CRUD lessons + link events
        └── topics.py            ← GET/POST /topics
```

### API Endpoints (highlights)
| Method | Path | Ghi chú |
|---|---|---|
| GET | `/api/v1/events/:slug` | Gọi nội bộ story-service để lấy story_json |
| GET | `/api/v1/eras/:slug/adjacent` | Era trước / sau |
| GET | `/api/v1/grades/:slug/lessons` | Danh sách bài SGK của 1 khối |
| GET | `/api/v1/events/featured` | Sự kiện nổi bật |

---

## 🧠 3. RAG Service (`services/rag/`)

### Nhiệm vụ
Quản lý toàn bộ pipeline **nhập liệu tài liệu và tìm kiếm ngữ nghĩa**:
upload file → parse (TXT/MD/PDF) → chunk → embed → lưu vector.

Khi AI Worker cần tìm chunks liên quan để generate story, nó gọi HTTP
nội bộ vào RAG Service để vector search.

### Bảng DB sở hữu
| Bảng | Mô tả |
|---|---|
| `source_documents` | File gốc (TXT / MD / PDF) admin upload |
| `event_sources` | Liên kết Event ↔ SourceDocument (truth source cho RAG) |
| `document_chunks` | Đoạn text sau khi chia nhỏ (600 tokens / chunk) |
| `chunk_embeddings` | Vector 1024-dim của từng chunk (pgvector HNSW) |

### Cấu trúc folder
```
services/rag/
├── Dockerfile
└── app/
    ├── main.py
    ├── core/
    │   └── settings.py          ← EMBED_MODEL, S3_*, NINEROUTER_*
    ├── models/
    │   └── models.py            ← SourceDocument, EventSource, DocumentChunk, ChunkEmbedding
    ├── parsers/
    │   └── document_parser.py   ← Factory: TxtParser, MarkdownParser, PdfParser (pymupdf)
    ├── schemas/
    │   ├── document.py          ← DocumentUploadResponse, SourceDocumentOut
    │   └── search.py            ← SearchQuery, ChunkResult
    ├── services/
    │   ├── chunker.py           ← Recursive text splitter (600 tokens, 80 overlap)
    │   ├── embedder.py          ← Gọi embedding model qua 9router
    │   ├── retriever.py         ← Vector search (ưu tiên event_sources, fallback)
    │   └── storage.py           ← Upload/download file từ MinIO/S3
    └── api/v1/
        ├── documents.py         ← POST /documents (upload), GET /documents
        ├── event_sources.py     ← Link Event ↔ SourceDocument
        └── search.py            ← GET /search, GET /search/semantic (admin debug)
```

### Luồng xử lý khi upload PDF cả quyển SGK
```
POST /api/v1/documents (multipart PDF)
  → validate mime, size, checksum duplicate
  → upload file → MinIO (raw-docs/{document_id}.pdf)
  → INSERT source_documents (status='uploaded')
  → INSERT generation_jobs (type='ingest')   ← enqueue cho ai-worker
  → 202 Accepted { document_id, job_id }
```

### API Endpoints
| Method | Path | Role |
|---|---|---|
| POST | `/api/v1/documents` | admin/editor |
| GET | `/api/v1/documents` | admin/editor |
| GET | `/api/v1/documents/:id/chunks` | admin/editor |
| POST | `/api/v1/events/:id/sources` | admin/editor |
| GET | `/api/v1/search?q=...` | public |
| GET | `/api/v1/search/semantic` | admin debug |

---

## 📖 4. Story Service (`services/story/`)

### Nhiệm vụ
Quản lý **phiên bản nội dung câu chuyện** (story versioning), hình ảnh AI,
và hàng đợi phê duyệt. Service này là nơi lưu trữ `story_json` —
dữ liệu mà Frontend render thành trang Event Detail.

### Bảng DB sở hữu
| Bảng | Mô tả |
|---|---|
| `event_story_versions` | Snapshot JSONB của story 6-beat |
| `block_citations` | Citation: block ↔ document_chunk (anti-hallucination) |
| `image_assets` | Metadata ảnh AI-gen hoặc admin upload |
| `review_items` | Hàng đợi phê duyệt story / block / image |

### Cấu trúc folder
```
services/story/
├── Dockerfile
└── app/
    ├── main.py
    ├── core/
    │   └── settings.py          ← S3_*
    ├── models/
    │   └── models.py            ← EventStoryVersion, BlockCitation, ImageAsset, ReviewItem
    ├── schemas/
    │   ├── story.py             ← StoryVersionOut, StoryJSON shape
    │   ├── image.py             ← ImageAssetOut
    │   └── review.py            ← ReviewItemOut
    ├── services/
    │   ├── story_service.py     ← publish, rollback, archive logic
    │   ├── publish_validator.py ← can_publish_story_version() — app-layer validation
    │   └── image_service.py     ← approve/reject image
    └── api/v1/
        ├── story_versions.py    ← GET/PATCH versions, publish, rollback
        ├── images.py            ← approve/reject/upload images
        └── review.py            ← GET/approve/reject review_items
```

### API Endpoints (highlights)
| Method | Path | Ghi chú |
|---|---|---|
| GET | `/api/v1/story/versions/:vId` | Full story_json + citations |
| POST | `/api/v1/story/versions/:vId/publish` | Chạy PublishValidator trước |
| POST | `/api/v1/story/versions/:vId/rollback` | Không mất data |
| POST | `/api/v1/images/:id/approve` | Chuyển status → approved |
| GET | `/api/v1/review-items?status=pending` | Hàng đợi cần duyệt |

---

## ⚙️ 5. AI Worker (`services/ai-worker/`)

### Nhiệm vụ
Background worker — **không nhận HTTP request từ ngoài**.
Liên tục poll bảng `generation_jobs` để thực thi các job nặng:
ingesting tài liệu, sinh story bằng LLM, sinh ảnh bằng DALL-E.

Giao tiếp với các service khác qua **HTTP nội bộ** (không JOIN DB chéo).

### Bảng DB sở hữu
| Bảng | Mô tả |
|---|---|
| `generation_jobs` | Queue table: ingest / story_version / image |

### Cấu trúc folder
```
services/ai-worker/
├── Dockerfile
└── app/
    ├── worker.py                ← Entry point: poll loop + dispatch
    ├── core/
    │   └── settings.py          ← NINEROUTER_*, *_SERVICE_URL, WORKER_*
    ├── models/
    │   └── models.py            ← GenerationJob (SELECT ... FOR UPDATE SKIP LOCKED)
    └── handlers/
        ├── ingest_handler.py    ← PDF parse → structure detect → chunk → embed
        ├── story_handler.py     ← RAG retrieve → LLM generate → citation validate
        └── image_handler.py     ← Prompt build → DALL-E → S3 → review queue
```

### Luồng Job Processing
```python
# worker.py — vòng lặp chính
while True:
    job = SELECT * FROM generation_jobs
          WHERE status='queued' AND attempts < max_attempts
          ORDER BY queued_at
          FOR UPDATE SKIP LOCKED
          LIMIT 1

    if job:
        dispatch(job)   # → ingest_handler / story_handler / image_handler
    else:
        await asyncio.sleep(POLL_INTERVAL)
```

### Luồng `ingest_handler` (PDF → Vector)
```
1. Lấy file PDF từ MinIO
2. PdfParser.extract() → plain text với ## headings
3. GPT-4o-mini: detect ranh giới bài học → [{lesson, title, page_start}]
4. Chunk theo boundary bài học (không cắt ngang bài)
5. Embed từng chunk → vector(1024)
6. POST http://sukyai-rag:8000/internal/chunks (bulk)
7. UPDATE source_documents status='embedded'
8. UPDATE generation_jobs status='succeeded'
```

### Luồng `story_handler` (RAG → Story JSON)
```
1. GET http://sukyai-content:8000/internal/events/{id} → metadata
2. GET http://sukyai-rag:8000/internal/retrieve → top-8 chunks liên quan
   (ưu tiên event_sources, fallback nếu < 3 chunks)
3. Với mỗi beat (hook→setup→rising→climax→falling→takeaway):
   a. Build prompt từ chunks + template
   b. LLM generate_json() → blocks[]
   c. Validate schema (Pydantic) + citation coverage ≥ 0.7
   d. Retry ≤ 2 lần nếu fail
4. POST http://sukyai-story:8000/internal/versions → lưu story_json
5. INSERT block_citations per block
6. INSERT review_items (status='pending')
7. UPDATE generation_jobs status='succeeded'
```

---

## 🌐 6. Shared Library (`shared/`)

Không phải service. Được **copy vào container của mỗi service** khi build.

```
shared/
└── core/
    ├── database.py   ← AsyncEngine, AsyncSession, Base, get_db()
    ├── settings.py   ← BaseServiceSettings (mọi service extend class này)
    └── security.py   ← verify_token(), require_role(), ok(), err()
```

**Cách dùng trong service:**
```python
# services/content/app/core/settings.py
from shared.core.settings import BaseServiceSettings

class Settings(BaseServiceSettings):
    STORY_SERVICE_URL: str = "http://sukyai-story:8000"

settings = Settings()
```

---

## 🐳 7. Infrastructure (`infra/`)

```
infra/
└── init.sql    ← Chạy 1 lần khi sukyai-db khởi động lần đầu
                   CREATE EXTENSION pgvector, pgcrypto, pg_trgm, unaccent
```

**Lưu ý**: Migration Alembic vẫn dùng folder `alembic/` ở root —
1 bộ migration duy nhất quản lý toàn bộ schema của cả 5 service.

---

## 🔄 Quy tắc giao tiếp giữa services

| Rule | Ví dụ |
|---|---|
| ✅ Gọi HTTP nội bộ để lấy data cross-service | `content-service` gọi `http://sukyai-story:8000/internal/...` |
| ✅ Mỗi service chỉ INSERT/UPDATE/DELETE bảng của mình | `story-service` không ghi vào bảng `events` |
| ❌ Cấm JOIN SQL giữa bảng của 2 service khác nhau | Không `JOIN events e ON esv.event_id = e.id` trong story-service |
| ❌ Cấm gọi trực tiếp DB của service khác | ai-worker không gọi `SELECT * FROM event_story_versions` — phải qua HTTP |

---

## 📋 Tóm tắt phân quyền

| Service | Bảng DB | Internal HTTP nhận từ |
|---|---|---|
| `auth` | users, audit_log | Gateway (public) |
| `content` | eras, grades, topics, lessons, events + junctions | Gateway (public) |
| `rag` | source_documents, event_sources, chunks, embeddings | Gateway + ai-worker |
| `story` | story_versions, citations, image_assets, review_items | Gateway + content + ai-worker |
| `ai-worker` | generation_jobs | — (chỉ poll DB, không nhận HTTP) |
