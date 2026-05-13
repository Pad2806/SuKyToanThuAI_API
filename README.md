# SuKyAI API — Backend Setup Guide

## Prerequisites

- Python 3.11+
- PostgreSQL 16 with pgvector extension
- S3-compatible storage (optional at Phase 1)

## Quick Start

```bash
# 1. Create virtual environment
cd SuKyAI_API
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate    # Linux/macOS

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env — fill in DATABASE_URL, NINEROUTER_API_KEY, etc.

# 4. Install pgvector on PostgreSQL (requires superuser)
# psql -U postgres -c "CREATE EXTENSION vector;"

# 5. Run migrations
alembic upgrade head

# 6. Seed baseline data
set SEED_ADMIN_PASSWORD=your-secure-password
python -m app.seeds

# 7. Start dev server
uvicorn app.main:app --reload --port 8000

# 8. Start worker (separate terminal)
python -m app.worker
```

## Project Structure

```
SuKyAI_API/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app shell
│   ├── config.py            # Pydantic settings (reads .env)
│   ├── database.py          # SQLAlchemy async engine + session
│   ├── models.py            # All ORM models (19 tables)
│   ├── seeds.py             # Baseline seed data
│   ├── ai/
│   │   └── provider.py      # AIProviderClient (9router adapter)
│   ├── services/
│   │   └── publish_validator.py  # PublishValidator
│   ├── utils/
│   │   └── text.py          # Vietnamese normalization
│   └── worker/
│       └── __main__.py      # PG-based worker (python -m app.worker)
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       ├── 001_enable_extensions.py
│       ├── 002_core_taxonomies.py
│       ├── 003_users.py
│       ├── 004_lessons.py
│       ├── 005_events_base.py
│       ├── 006_junction_tables.py
│       ├── 007_source_documents.py
│       ├── 008_chunks_and_embeddings.py
│       ├── 009_story_versions.py
│       ├── 010_image_assets.py
│       ├── 011_add_published_fk.py
│       ├── 012_generation_jobs.py
│       └── 013_review_audit_indexes.py
├── docs/
│   ├── hld.md               # High-Level Design
│   └── database-schema.md   # Full schema reference
├── alembic.ini
├── requirements.txt
└── .env.example
```

## Migration Order (Critical)

Migrations run in dependency order to avoid circular FKs:

```
001 extensions → 002 taxonomies → 003 users → 004 lessons
→ 005 events (no published_version_id FK) → 006 junctions
→ 007 source_documents + event_sources → 008 chunks + embeddings
→ 009 story_versions + citations → 010 image_assets
→ 011 ADD FK events.published_story_version_id  ← deferred
→ 012 generation_jobs → 013 review + audit + search_index + trigger
```

## Running the Worker

```bash
# Single worker (development)
python -m app.worker

# Multiple workers (production — each claims different jobs via SKIP LOCKED)
WORKER_ID=worker-001 python -m app.worker &
WORKER_ID=worker-002 python -m app.worker &
```

## API Endpoints (Phase 2 — to be implemented)

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/events` | List published events (paginated) |
| GET | `/api/v1/events/{slug}` | Event detail + published story |
| GET | `/api/v1/eras` | All eras (ordered) |
| GET | `/api/v1/eras/{slug}/events` | Events in era |
| GET | `/api/v1/topics` | All topics |
| GET | `/api/v1/topics/{slug}/events` | Events by topic |
| GET | `/api/v1/grades/{level}/events` | Events by grade |
| GET | `/api/v1/search` | Accent-insensitive search |
| POST | `/api/v1/admin/documents` | Upload source document |
| POST | `/api/v1/admin/events/{id}/generate-story` | Trigger story gen job |
| PATCH | `/api/v1/admin/story-versions/{id}/review` | Approve/reject |
| POST | `/api/v1/admin/story-versions/{id}/publish` | Publish (runs validator) |
| GET | `/health` | Health check |

## Frontend Compatibility

Response shapes are compatible with `SuKyAI_Web/src/lib/event-queries.js` contracts:

- `getEventsByEra(eraSlug)` → `GET /api/v1/eras/{slug}/events`
- `getFeaturedEvents()` → `GET /api/v1/events?featured=true`
- `getEventBySlug(slug)` → `GET /api/v1/events/{slug}`
- `getAllEras()` → `GET /api/v1/eras`
- `getAllTopics()` → `GET /api/v1/topics`
- `searchEvents({ q, filters })` → `GET /api/v1/search?q=...&era=...`

Swap mock → API: **no component changes needed**.

## Security Notes

- Never commit `.env` to git (it's in `.gitignore`)
- JWT tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES`
- All admin endpoints require `role IN ('admin', 'editor')`
- AI worker never sets `featured=true` on events
- PublishValidator requires human approval before any story goes public
