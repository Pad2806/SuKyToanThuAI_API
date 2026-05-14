# SuKyAI Platform — Backend Microservices HLD

## Architecture Overview

```mermaid
graph TB
    FE["🖥️ SuKyAI Web<br/>(React + Vite)<br/>localhost:5173"]

    subgraph Docker Network: sukyai_net
        GW["🚪 Gateway<br/>:8000<br/>FastAPI reverse proxy"]

        subgraph Services
            AUTH["🔐 auth-service<br/>:8001<br/>JWT · Users"]
            CONTENT["📜 content-service<br/>:8002<br/>Events · Eras · Grades"]
            RAG["🧠 rag-service<br/>:8003<br/>Documents · Chunks · Vectors"]
            STORY["📖 story-service<br/>:8004<br/>Versions · Review · Images"]
            WORKER["⚙️ ai-worker<br/>background<br/>Job Processor"]
        end

        DB[("🐘 PostgreSQL 16<br/>+ pgvector<br/>Schemas: auth·content·rag·story·ai")]
        MINIO["🗄️ MinIO<br/>Object Storage<br/>:9000"]
    end

    FE -->|"HTTPS /api/v1/*"| GW
    GW -->|"/api/v1/auth/*<br/>/api/v1/users/*"| AUTH
    GW -->|"/api/v1/events/*<br/>/api/v1/eras/*<br/>/api/v1/grades/*<br/>/api/v1/lessons/*<br/>/api/v1/topics/*"| CONTENT
    GW -->|"/api/v1/documents/*<br/>/api/v1/rag/*"| RAG
    GW -->|"/api/v1/story/*<br/>/api/v1/images/*<br/>/api/v1/review-items/*"| STORY

    AUTH --> DB
    CONTENT --> DB
    RAG --> DB
    STORY --> DB
    WORKER --> DB

    CONTENT -->|"HTTP internal<br/>GET published story"| STORY
    WORKER -->|"HTTP internal<br/>GET event metadata"| CONTENT
    WORKER -->|"HTTP internal<br/>vector search"| RAG
    WORKER -->|"HTTP internal<br/>POST story version"| STORY

    RAG --> MINIO
    STORY --> MINIO
    WORKER --> MINIO
```

---

## Service Responsibility Matrix

| Service | DB Schema | Port | Owns | Calls |
|---|---|---|---|---|
| `gateway` | — | 8000 (public) | Route table | All services |
| `auth-service` | `auth` | 8001 | users, audit_log | — |
| `content-service` | `content` | 8002 | eras, grades, lessons, topics, events, event_sources | story-service |
| `rag-service` | `rag` | 8003 | source_documents, document_chunks, chunk_embeddings | — |
| `story-service` | `story` | 8004 | event_story_versions, block_citations, image_assets, review_items | content-service, rag-service |
| `ai-worker` | `ai` | 8005 (optional) | generation_jobs | content, rag, story |

---

## Database Schema Ownership

```
PostgreSQL: sukyai
├── auth.*
│   ├── users
│   └── audit_log
├── content.*
│   ├── eras
│   ├── grades
│   ├── lessons
│   ├── topics
│   ├── events
│   ├── event_topics
│   ├── event_grades
│   ├── lesson_events
│   └── event_sources         ← UUID ref to rag.source_documents (no FK)
├── rag.*
│   ├── source_documents
│   ├── document_chunks
│   └── chunk_embeddings      ← vector(1024) via pgvector
├── story.*
│   ├── event_story_versions  ← UUID ref to content.events (no FK)
│   ├── block_citations       ← UUID ref to rag.document_chunks (no FK)
│   ├── image_assets
│   └── review_items
└── ai.*
    └── generation_jobs       ← UUID refs to all other schemas (no FK)
```

> **Cross-service FK rule**: No hard FK across schemas.
> UUID references are validated at application layer via internal HTTP calls.

---

## Internal Communication Pattern

```mermaid
sequenceDiagram
    participant FE as Frontend
    participant GW as Gateway
    participant CS as content-service
    participant SS as story-service
    participant RG as rag-service
    participant WK as ai-worker
    participant DB as PostgreSQL

    Note over FE,DB: GET /api/v1/events/chien-thang-bach-dang
    FE->>GW: GET /api/v1/events/:slug
    GW->>CS: forward request
    CS->>DB: SELECT * FROM content.events WHERE slug=?
    CS->>SS: GET /internal/events/{id}/published-story
    SS->>DB: SELECT FROM story.event_story_versions WHERE event_id=? AND status='published'
    SS-->>CS: {story_json}
    CS-->>GW: {event + story}
    GW-->>FE: 200 {data: {...}}

    Note over FE,DB: POST /api/v1/documents (upload PDF)
    FE->>GW: POST /api/v1/documents (multipart)
    GW->>RG: forward
    RG->>DB: INSERT rag.source_documents
    RG->>DB: INSERT ai.generation_jobs (type='document_ingestion')
    RG-->>FE: 202 {document_id, job_id}

    Note over WK,DB: Background: process ingest job
    WK->>DB: SELECT ai.generation_jobs FOR UPDATE SKIP LOCKED
    WK->>RG: GET /internal/documents/{id}/download
    WK->>WK: PDF parse → chunk → embed
    WK->>RG: POST /internal/chunks (bulk)
    WK->>DB: UPDATE ai.generation_jobs SET status='succeeded'
```

---

## AI Worker Job Flow

```mermaid
flowchart TD
    START([Poll every 5s]) --> QUERY["SELECT FROM ai.generation_jobs<br/>WHERE status='queued'<br/>FOR UPDATE SKIP LOCKED"]
    QUERY --> HAS_JOB{Job found?}
    HAS_JOB -->|No| SLEEP[Sleep 5s] --> START
    HAS_JOB -->|Yes| LOCK["UPDATE status='running'<br/>locked_by=worker_id<br/>attempts=attempts+1"]
    LOCK --> TYPE{job.type}
    TYPE -->|document_ingestion| INGEST["IngestHandler<br/>parse→chunk→embed"]
    TYPE -->|story_generation| STORY["StoryHandler<br/>RAG→LLM→save version"]
    TYPE -->|image_generation| IMAGE["ImageHandler<br/>prompt→DALL-E→S3"]
    INGEST --> SUCCESS
    STORY --> SUCCESS
    IMAGE --> SUCCESS
    INGEST -->|error| FAIL
    STORY -->|error| FAIL
    IMAGE -->|error| FAIL
    SUCCESS["status='succeeded'<br/>finished_at=now()"] --> START
    FAIL{attempts < max?} -->|Yes| RETRY["status='queued'<br/>log error"] --> START
    FAIL -->|No| DEAD["status='failed'<br/>finished_at=now()"] --> START
```

---

## Gateway Route Table

| Prefix | Upstream |
|---|---|
| `/api/v1/auth` | `http://auth-service:8001` |
| `/api/v1/users` | `http://auth-service:8001` |
| `/api/v1/events` | `http://content-service:8002` |
| `/api/v1/eras` | `http://content-service:8002` |
| `/api/v1/grades` | `http://content-service:8002` |
| `/api/v1/lessons` | `http://content-service:8002` |
| `/api/v1/topics` | `http://content-service:8002` |
| `/api/v1/documents` | `http://rag-service:8003` |
| `/api/v1/rag` | `http://rag-service:8003` |
| `/api/v1/story` | `http://story-service:8004` |
| `/api/v1/images` | `http://story-service:8004` |
| `/api/v1/review-items` | `http://story-service:8004` |
| `/api/v1/ai` | `http://ai-worker:8005` |

---

## Health Endpoints

All services expose `GET /health`:

```json
{"status": "ok", "service": "auth-service"}
```

Check all services at once:
```bash
for svc in gateway auth-service content-service rag-service story-service; do
  curl -s http://localhost:$(docker port sukyai-$svc 8000/tcp | cut -d: -f2)/health
done
```

---

## Running Locally

```bash
# 1. Copy and configure env
cp .env.example .env

# 2. Start all services
docker compose up -d

# 3. Run migrations
docker compose exec auth-service alembic upgrade head

# 4. Check health
curl http://localhost:8000/health

# 5. View logs
docker compose logs -f ai-worker
```

---

## Migration Strategy (Phase 1)

One shared Alembic root (`alembic/`) managing all schemas.

Migration naming convention:
```
001_auth_users.py
002_auth_audit_log.py
003_content_eras_grades_topics.py
004_content_lessons.py
005_content_events.py
006_content_junctions.py
007_content_event_sources.py
008_rag_source_documents.py
009_rag_chunks_embeddings.py
010_story_versions_citations.py
011_story_images_review.py
012_ai_generation_jobs.py
```

Each migration prefixes tables with schema name:
```python
op.create_table("users", schema="auth", ...)
op.create_table("events", schema="content", ...)
```
