# Database Schema Design — Sử Ký Toàn Thư AI

> **Version**: 1.0 — Phase 1  
> **Engine**: PostgreSQL 16 + pgvector  
> **Extensions**: `pgcrypto`, `vector`, `pg_trgm`, `unaccent`

---

## ERD — Entity Relationship Diagram

```mermaid
erDiagram
    users {
        uuid id PK
        text email UK
        text password_hash
        text role
        text display_name
        bool active
        timestamptz created_at
        timestamptz last_login_at
    }

    eras {
        uuid id PK
        text slug UK
        text name
        text year_range
        int start_year
        int end_year
        text summary
        text cover_image
        text fallback_image
        int order_index
        timestamptz created_at
        timestamptz updated_at
    }

    grades {
        uuid id PK
        int level UK
        text slug UK
        text name
        text description
        int order_index
        timestamptz created_at
    }

    topics {
        uuid id PK
        text slug UK
        text name
        text description
        text cover_image
    }

    lessons {
        uuid id PK
        uuid grade_id FK
        text slug
        text title
        int lesson_order
        text part
        text chapter
        text summary
        text cover_image
        timestamptz created_at
        timestamptz updated_at
        timestamptz deleted_at
        uuid deleted_by FK
    }

    events {
        uuid id PK
        text slug
        text title
        uuid era_id FK
        int year
        int start_year
        int end_year
        text type
        bool featured
        text summary
        text excerpt
        text image
        text fallback_image
        text location
        text[] actors
        text[] grade_tags
        text status
        jsonb interactive_data
        text template_type
        uuid published_story_version_id FK
        text normalized_title
        text normalized_summary
        text normalized_search_text
        timestamptz published_at
        timestamptz created_at
        timestamptz updated_at
        timestamptz deleted_at
        uuid deleted_by FK
    }

    event_topics {
        uuid event_id FK
        uuid topic_id FK
    }

    event_grades {
        uuid event_id FK
        uuid grade_id FK
    }

    lesson_events {
        uuid lesson_id FK
        uuid event_id FK
        int event_order
    }

    source_documents {
        uuid id PK
        text title
        text source_type
        text grade_hint
        text era_hint
        text storage_url
        text checksum UK
        text mime_type
        bigint size_bytes
        text status
        uuid uploaded_by FK
        timestamptz uploaded_at
        timestamptz processed_at
        timestamptz deleted_at
        uuid deleted_by FK
    }

    event_sources {
        uuid id PK
        uuid event_id FK
        uuid source_document_id FK
        text relation_type
        int priority
        timestamptz created_at
        uuid created_by FK
    }

    document_chunks {
        uuid id PK
        uuid document_id FK
        int chunk_index
        text content
        int token_count
        text section_title
        int page_or_lesson_hint
        jsonb metadata
        timestamptz created_at
    }

    chunk_embeddings {
        uuid chunk_id PK FK
        vector embedding
        text model
        int dim
        timestamptz created_at
    }

    event_story_versions {
        uuid id PK
        uuid event_id FK
        int version
        jsonb story_json
        text status
        uuid created_by FK
        timestamptz created_at
        timestamptz published_at
        text notes
        timestamptz deleted_at
        uuid deleted_by FK
    }

    block_citations {
        uuid id PK
        uuid event_story_version_id FK
        uuid block_id
        uuid chunk_id FK
        numeric similarity
        int rank
        timestamptz created_at
    }

    image_assets {
        uuid id PK
        text storage_url
        text thumbnail_url
        text source
        text prompt
        text model
        int width
        int height
        text status
        text caption
        text alt_text
        timestamptz created_at
        timestamptz approved_at
        uuid approved_by FK
        timestamptz deleted_at
        uuid deleted_by FK
    }

    generation_jobs {
        uuid id PK
        text type
        uuid event_id FK
        uuid event_story_version_id FK
        uuid image_asset_id FK
        uuid source_document_id FK
        text status
        jsonb input
        jsonb output
        text error
        int attempts
        int max_attempts
        text locked_by
        timestamptz locked_at
        timestamptz queued_at
        timestamptz started_at
        timestamptz finished_at
    }

    review_items {
        uuid id PK
        text entity_type
        text entity_id
        text review_type
        text status
        text reviewer_notes
        uuid created_by FK
        uuid reviewed_by FK
        timestamptz created_at
        timestamptz reviewed_at
    }

    audit_log {
        uuid id PK
        uuid actor_id FK
        text action
        text entity_type
        uuid entity_id
        jsonb diff
        timestamptz created_at
    }

    eras ||--o{ events : "has"
    grades ||--o{ lessons : "has"
    grades ||--o{ event_grades : "tagged_in"
    topics ||--o{ event_topics : "tagged_in"
    events ||--o{ event_topics : "tagged_with"
    events ||--o{ event_grades : "tagged_with"
    events ||--o{ lesson_events : "part_of"
    lessons ||--o{ lesson_events : "contains"
    events ||--o{ event_sources : "sourced_from"
    source_documents ||--o{ event_sources : "referenced_by"
    source_documents ||--o{ document_chunks : "split_into"
    document_chunks ||--|| chunk_embeddings : "has_embedding"
    events ||--o{ event_story_versions : "has_versions"
    event_story_versions ||--o{ block_citations : "cited_by"
    document_chunks ||--o{ block_citations : "cited_in"
    events ||--o{ generation_jobs : "triggers"
    event_story_versions ||--o{ generation_jobs : "targets"
    image_assets ||--o{ generation_jobs : "targets"
    source_documents ||--o{ generation_jobs : "targets"
    users ||--o{ source_documents : "uploaded"
    users ||--o{ event_sources : "created"
    users ||--o{ event_story_versions : "authored"
    users ||--o{ review_items : "created"
    users ||--o{ review_items : "reviews"
    users ||--o{ image_assets : "approved"
    users ||--o{ audit_log : "performs"
```

---

## Table Definitions

### Table: `users`
```sql
CREATE TABLE users (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    email         text UNIQUE NOT NULL,
    password_hash text NOT NULL,
    role          text NOT NULL CHECK (role IN ('admin', 'editor', 'viewer')),
    display_name  text NOT NULL,
    active        boolean NOT NULL DEFAULT true,
    created_at    timestamptz NOT NULL DEFAULT now(),
    last_login_at timestamptz
);
```

### Table: `eras`
```sql
CREATE TABLE eras (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug           text UNIQUE NOT NULL,
    name           text NOT NULL,
    year_range     text NOT NULL,
    start_year     int NOT NULL,
    end_year       int NOT NULL,
    summary        text NOT NULL,
    cover_image    text NOT NULL,
    fallback_image text,
    order_index    int NOT NULL DEFAULT 0,
    created_at     timestamptz NOT NULL DEFAULT now(),
    updated_at     timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT eras_years_check CHECK (end_year >= start_year)
);
```

### Table: `grades`
```sql
CREATE TABLE grades (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    level       int UNIQUE NOT NULL CHECK (level BETWEEN 5 AND 12),
    slug        text UNIQUE NOT NULL,
    name        text NOT NULL,
    description text,
    order_index int NOT NULL DEFAULT 0,
    created_at  timestamptz NOT NULL DEFAULT now()
);
```

### Table: `topics`
```sql
CREATE TABLE topics (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug        text UNIQUE NOT NULL,
    name        text NOT NULL,
    description text,
    cover_image text
);
```

### Table: `lessons`
```sql
CREATE TABLE lessons (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    grade_id     uuid NOT NULL REFERENCES grades(id),
    slug         text NOT NULL,
    title        text NOT NULL,
    lesson_order int NOT NULL,
    part         text,
    chapter      text,
    summary      text,
    cover_image  text,
    created_at   timestamptz NOT NULL DEFAULT now(),
    updated_at   timestamptz NOT NULL DEFAULT now(),
    deleted_at   timestamptz,
    deleted_by   uuid REFERENCES users(id),
    CONSTRAINT lessons_slug_unique UNIQUE NULLS NOT DISTINCT (grade_id, slug, deleted_at)
    -- Application enforces: unique(grade_id, slug) where deleted_at is null
);

CREATE INDEX idx_lessons_grade_order ON lessons (grade_id, lesson_order)
    WHERE deleted_at IS NULL;
```

### Table: `events`
```sql
CREATE TABLE events (
    id                          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    slug                        text NOT NULL,
    title                       text NOT NULL,
    era_id                      uuid REFERENCES eras(id),
    year                        int NOT NULL,
    start_year                  int,
    end_year                    int,
    type                        text NOT NULL DEFAULT 'other'
                                    CHECK (type IN ('battle','dynasty','movement','culture','diplomacy','other')),
    featured                    boolean NOT NULL DEFAULT false,
    summary                     text NOT NULL,
    excerpt                     text NOT NULL,
    image                       text NOT NULL,
    fallback_image              text,
    location                    text,
    actors                      text[] NOT NULL DEFAULT '{}',
    grade_tags                  text[] NOT NULL DEFAULT '{}',
    status                      text NOT NULL DEFAULT 'draft'
                                    CHECK (status IN ('draft','review','published','archived')),
    interactive_data            jsonb NOT NULL DEFAULT '{}',
    template_type               text NOT NULL DEFAULT 'universal'
                                    CHECK (template_type IN ('universal','battle','dynasty','movement','culture','diplomacy')),
    published_story_version_id  uuid,  -- FK added later after event_story_versions
    normalized_title            text NOT NULL DEFAULT '',
    normalized_summary          text NOT NULL DEFAULT '',
    normalized_search_text      text NOT NULL DEFAULT '',
    published_at                timestamptz,
    created_at                  timestamptz NOT NULL DEFAULT now(),
    updated_at                  timestamptz NOT NULL DEFAULT now(),
    deleted_at                  timestamptz,
    deleted_by                  uuid REFERENCES users(id),
    CONSTRAINT events_year_range_check CHECK (
        (start_year IS NULL AND end_year IS NULL)
        OR (start_year IS NOT NULL AND end_year IS NOT NULL AND end_year >= start_year)
    )
);

-- Unique slug when not soft-deleted
CREATE UNIQUE INDEX idx_events_slug_active ON events (slug)
    WHERE deleted_at IS NULL;
```

### Table: `event_topics`
```sql
CREATE TABLE event_topics (
    event_id uuid NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    topic_id uuid NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, topic_id)
);
```

### Table: `event_grades`
```sql
CREATE TABLE event_grades (
    event_id uuid NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    grade_id uuid NOT NULL REFERENCES grades(id) ON DELETE CASCADE,
    PRIMARY KEY (event_id, grade_id)
);
```

### Table: `lesson_events`
```sql
CREATE TABLE lesson_events (
    lesson_id   uuid NOT NULL REFERENCES lessons(id) ON DELETE CASCADE,
    event_id    uuid NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    event_order int NOT NULL,
    PRIMARY KEY (lesson_id, event_id)
);
```

### Table: `source_documents`
```sql
CREATE TABLE source_documents (
    id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title        text NOT NULL,
    source_type  text NOT NULL DEFAULT 'sgk'
                     CHECK (source_type IN ('sgk','reference','other')),
    grade_hint   text,
    era_hint     text,
    storage_url  text NOT NULL,
    checksum     text UNIQUE NOT NULL,
    mime_type    text NOT NULL CHECK (mime_type IN ('text/markdown','text/plain')),
    size_bytes   bigint NOT NULL CHECK (size_bytes > 0),
    status       text NOT NULL DEFAULT 'uploaded'
                     CHECK (status IN ('uploaded','chunked','embedded','failed')),
    uploaded_by  uuid REFERENCES users(id),
    uploaded_at  timestamptz NOT NULL DEFAULT now(),
    processed_at timestamptz,
    deleted_at   timestamptz,
    deleted_by   uuid REFERENCES users(id)
);
```

### Table: `event_sources`
```sql
CREATE TABLE event_sources (
    id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id           uuid NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    source_document_id uuid NOT NULL REFERENCES source_documents(id) ON DELETE RESTRICT,
    relation_type      text NOT NULL DEFAULT 'primary_source'
                           CHECK (relation_type IN ('primary_source','secondary_source','reference','teacher_note')),
    priority           int NOT NULL DEFAULT 0,
    created_at         timestamptz NOT NULL DEFAULT now(),
    created_by         uuid REFERENCES users(id),
    UNIQUE (event_id, source_document_id)
);

CREATE INDEX idx_event_sources_event ON event_sources (event_id, priority DESC, relation_type);
```

### Table: `document_chunks`
```sql
CREATE TABLE document_chunks (
    id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id         uuid NOT NULL REFERENCES source_documents(id) ON DELETE CASCADE,
    chunk_index         int NOT NULL CHECK (chunk_index >= 0),
    content             text NOT NULL,
    token_count         int NOT NULL CHECK (token_count > 0),
    section_title       text,
    page_or_lesson_hint int,
    metadata            jsonb NOT NULL DEFAULT '{}',
    created_at          timestamptz NOT NULL DEFAULT now(),
    UNIQUE (document_id, chunk_index)
);
```

### Table: `chunk_embeddings`
```sql
CREATE TABLE chunk_embeddings (
    chunk_id   uuid PRIMARY KEY REFERENCES document_chunks(id) ON DELETE CASCADE,
    embedding  vector(1024) NOT NULL,
    model      text NOT NULL,
    dim        int NOT NULL DEFAULT 1024 CHECK (dim = 1024),
    created_at timestamptz NOT NULL DEFAULT now()
);

-- HNSW index for fast ANN cosine search
CREATE INDEX idx_chunk_embeddings_hnsw ON chunk_embeddings
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

### Table: `event_story_versions`
```sql
CREATE TABLE event_story_versions (
    id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id   uuid NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    version    int NOT NULL CHECK (version >= 1),
    story_json jsonb NOT NULL,
    status     text NOT NULL DEFAULT 'draft'
                   CHECK (status IN ('draft','review','published','archived')),
    created_by uuid REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz,
    notes      text,
    deleted_at timestamptz,
    deleted_by uuid REFERENCES users(id),
    -- Only one active version per (event, version number)
    CONSTRAINT esv_version_unique UNIQUE NULLS NOT DISTINCT (event_id, version, deleted_at)
);

-- Enforce single published version per event (application also validates)
CREATE UNIQUE INDEX idx_esv_one_published ON event_story_versions (event_id)
    WHERE status = 'published' AND deleted_at IS NULL;
```

### Table: `block_citations`
```sql
CREATE TABLE block_citations (
    id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    event_story_version_id uuid NOT NULL REFERENCES event_story_versions(id) ON DELETE CASCADE,
    block_id               uuid NOT NULL,
    chunk_id               uuid NOT NULL REFERENCES document_chunks(id) ON DELETE RESTRICT,
    similarity             numeric(4,3) CHECK (similarity BETWEEN 0 AND 1),
    rank                   int NOT NULL CHECK (rank >= 1),
    created_at             timestamptz NOT NULL DEFAULT now(),
    UNIQUE (event_story_version_id, block_id, chunk_id)
);

CREATE INDEX idx_block_citations_version_block ON block_citations (event_story_version_id, block_id);
```

### Table: `image_assets`
```sql
CREATE TABLE image_assets (
    id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    storage_url   text NOT NULL,
    thumbnail_url text,
    source        text NOT NULL CHECK (source IN ('ai_generated','admin_upload','stock')),
    prompt        text,
    model         text,
    width         int,
    height        int,
    status        text NOT NULL DEFAULT 'pending'
                      CHECK (status IN ('pending','approved','rejected')),
    caption       text,
    alt_text      text NOT NULL DEFAULT '',
    created_at    timestamptz NOT NULL DEFAULT now(),
    approved_at   timestamptz,
    approved_by   uuid REFERENCES users(id),
    deleted_at    timestamptz,
    deleted_by    uuid REFERENCES users(id)
);
```

### Table: `generation_jobs`
```sql
CREATE TABLE generation_jobs (
    id                     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    type                   text NOT NULL CHECK (type IN ('ingest','story_version','image')),
    event_id               uuid REFERENCES events(id),
    event_story_version_id uuid REFERENCES event_story_versions(id),
    image_asset_id         uuid REFERENCES image_assets(id),
    source_document_id     uuid REFERENCES source_documents(id),
    status                 text NOT NULL DEFAULT 'queued'
                               CHECK (status IN ('queued','running','succeeded','failed','cancelled')),
    input                  jsonb NOT NULL,
    output                 jsonb,
    error                  text,
    attempts               int NOT NULL DEFAULT 0,
    max_attempts           int NOT NULL DEFAULT 3,
    locked_by              text,
    locked_at              timestamptz,
    queued_at              timestamptz NOT NULL DEFAULT now(),
    started_at             timestamptz,
    finished_at            timestamptz
);

CREATE INDEX idx_jobs_status ON generation_jobs (status, queued_at);
CREATE INDEX idx_jobs_type_status ON generation_jobs (type, status);
CREATE INDEX idx_jobs_locked_at ON generation_jobs (locked_at)
    WHERE status = 'running';
```

### Table: `review_items`
```sql
CREATE TABLE review_items (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type    text NOT NULL CHECK (entity_type IN (
                       'story_version','story_block','image_asset','comic_scene','slide_page'
                   )),
    entity_id      text NOT NULL,
    review_type    text NOT NULL CHECK (review_type IN (
                       'content_accuracy','image_quality','citation_check','publish_approval'
                   )),
    status         text NOT NULL DEFAULT 'pending'
                       CHECK (status IN ('pending','approved','rejected')),
    reviewer_notes text,
    created_by     uuid REFERENCES users(id),
    reviewed_by    uuid REFERENCES users(id),
    created_at     timestamptz NOT NULL DEFAULT now(),
    reviewed_at    timestamptz
);

CREATE INDEX idx_review_items_status ON review_items (status, created_at DESC);
CREATE INDEX idx_review_items_entity ON review_items (entity_type, entity_id);
```

### Table: `audit_log`
```sql
CREATE TABLE audit_log (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    actor_id    uuid REFERENCES users(id),
    action      text NOT NULL,
    entity_type text NOT NULL,
    entity_id   uuid NOT NULL,
    diff        jsonb,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_audit_log_entity ON audit_log (entity_type, entity_id, created_at DESC);
CREATE INDEX idx_audit_log_actor ON audit_log (actor_id, created_at DESC);
```

---

## Events Indexes (Complete)

```sql
-- Era filter
CREATE INDEX idx_events_era_id ON events (era_id) WHERE deleted_at IS NULL;

-- Year ordering
CREATE INDEX idx_events_year ON events (year) WHERE deleted_at IS NULL;

-- Status filter
CREATE INDEX idx_events_status ON events (status) WHERE deleted_at IS NULL;

-- Featured flag
CREATE INDEX idx_events_featured ON events (featured) WHERE deleted_at IS NULL AND featured = true;

-- Array contains for grade_tags (GIN)
CREATE INDEX idx_events_grade_tags ON events USING GIN (grade_tags) WHERE deleted_at IS NULL;

-- Array contains for actors (GIN)
CREATE INDEX idx_events_actors ON events USING GIN (actors) WHERE deleted_at IS NULL;

-- Full trigram search on normalized text
CREATE INDEX idx_events_normalized_search ON events
USING GIN (normalized_search_text gin_trgm_ops)
WHERE deleted_at IS NULL;
```

---

## DB Trigger — Immutable Published Story JSON

```sql
CREATE OR REPLACE FUNCTION prevent_published_story_edit()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.status = 'published' AND NEW.story_json IS DISTINCT FROM OLD.story_json THEN
        RAISE EXCEPTION 'Cannot edit story_json of a published event_story_version (id=%)', OLD.id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_prevent_published_story_edit
BEFORE UPDATE ON event_story_versions
FOR EACH ROW EXECUTE FUNCTION prevent_published_story_edit();
```

---

## story_json Shape Reference

```json
{
  "templateType": "battle",
  "beats": [
    {
      "type": "hook",
      "title": "Khoảnh khắc lịch sử",
      "blocks": [
        {
          "id": "550e8400-e29b-41d4-a716-446655440000",
          "type": "text",
          "data": { "body": "..." },
          "citationIds": ["chunk-uuid-1"],
          "imageAssetId": null,
          "confidence": 0.92,
          "status": "approved"
        }
      ]
    }
  ]
}
```

**Block status values:** `draft` | `approved` | `rejected` | `manual_required`  
**Rules:**
- `manual_required` blocks are never public-renderable
- PublishValidator checks all public blocks have `status = 'approved'`
