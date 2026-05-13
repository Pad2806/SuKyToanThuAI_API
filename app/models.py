"""
SQLAlchemy 2 async ORM models for SuKyAI API.
All tables use UUID PKs generated via gen_random_uuid() (pgcrypto).
Soft-delete pattern: deleted_at + deleted_by on mutable entities.
"""
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )


def _now() -> Mapped[datetime]:
    return mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


def _nullable_ts() -> Mapped[datetime | None]:
    return mapped_column(TIMESTAMP(timezone=True), nullable=True)


# ─────────────────────────────────────────────
#  users
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = _uuid_pk()
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("true"))
    created_at: Mapped[datetime] = _now()
    last_login_at: Mapped[datetime | None] = _nullable_ts()

    __table_args__ = (
        CheckConstraint("role IN ('admin','editor','viewer')", name="users_role_check"),
    )


# ─────────────────────────────────────────────
#  eras
# ─────────────────────────────────────────────

class Era(Base):
    __tablename__ = "eras"

    id: Mapped[uuid.UUID] = _uuid_pk()
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    year_range: Mapped[str] = mapped_column(Text, nullable=False)
    start_year: Mapped[int] = mapped_column(Integer, nullable=False)
    end_year: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    cover_image: Mapped[str] = mapped_column(Text, nullable=False)
    fallback_image: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()

    events: Mapped[list["Event"]] = relationship(back_populates="era")

    __table_args__ = (
        CheckConstraint("end_year >= start_year", name="eras_years_check"),
    )


# ─────────────────────────────────────────────
#  grades
# ─────────────────────────────────────────────

class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[uuid.UUID] = _uuid_pk()
    level: Mapped[int] = mapped_column(Integer, unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = _now()

    __table_args__ = (
        CheckConstraint("level BETWEEN 5 AND 12", name="grades_level_check"),
    )


# ─────────────────────────────────────────────
#  topics
# ─────────────────────────────────────────────

class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = _uuid_pk()
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    cover_image: Mapped[str | None] = mapped_column(Text)


# ─────────────────────────────────────────────
#  lessons
# ─────────────────────────────────────────────

class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[uuid.UUID] = _uuid_pk()
    grade_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grades.id"), nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    lesson_order: Mapped[int] = mapped_column(Integer, nullable=False)
    part: Mapped[str | None] = mapped_column(Text)
    chapter: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    cover_image: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()
    deleted_at: Mapped[datetime | None] = _nullable_ts()
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    grade: Mapped[Grade] = relationship()

    __table_args__ = (
        Index("idx_lessons_grade_order", "grade_id", "lesson_order",
              postgresql_where=text("deleted_at IS NULL")),
    )


# ─────────────────────────────────────────────
#  events
# ─────────────────────────────────────────────

class Event(Base):
    __tablename__ = "events"

    id: Mapped[uuid.UUID] = _uuid_pk()
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    era_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("eras.id"))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    start_year: Mapped[int | None] = mapped_column(Integer)
    end_year: Mapped[int | None] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'other'"))
    featured: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    image: Mapped[str] = mapped_column(Text, nullable=False)
    fallback_image: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    actors: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default=text("'{}'"))
    grade_tags: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default=text("'{}'"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'draft'"))
    interactive_data: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'"))
    template_type: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'universal'"))
    published_story_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("event_story_versions.id", use_alter=True, name="fk_events_published_version"),
    )
    normalized_title: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    normalized_summary: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    normalized_search_text: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    published_at: Mapped[datetime | None] = _nullable_ts()
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()
    deleted_at: Mapped[datetime | None] = _nullable_ts()
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    era: Mapped[Era | None] = relationship(back_populates="events")
    story_versions: Mapped[list["EventStoryVersion"]] = relationship(
        back_populates="event",
        foreign_keys="EventStoryVersion.event_id",
    )
    published_version: Mapped["EventStoryVersion | None"] = relationship(
        foreign_keys=[published_story_version_id],
    )

    __table_args__ = (
        CheckConstraint(
            "type IN ('battle','dynasty','movement','culture','diplomacy','other')",
            name="events_type_check",
        ),
        CheckConstraint(
            "status IN ('draft','review','published','archived')",
            name="events_status_check",
        ),
        CheckConstraint(
            "template_type IN ('universal','battle','dynasty','movement','culture','diplomacy')",
            name="events_template_check",
        ),
        CheckConstraint(
            "(start_year IS NULL AND end_year IS NULL) OR "
            "(start_year IS NOT NULL AND end_year IS NOT NULL AND end_year >= start_year)",
            name="events_year_range_check",
        ),
        Index("idx_events_slug_active", "slug",
              unique=True, postgresql_where=text("deleted_at IS NULL")),
        Index("idx_events_era_id", "era_id",
              postgresql_where=text("deleted_at IS NULL")),
        Index("idx_events_year", "year",
              postgresql_where=text("deleted_at IS NULL")),
        Index("idx_events_status", "status",
              postgresql_where=text("deleted_at IS NULL")),
        Index("idx_events_featured", "featured",
              postgresql_where=text("deleted_at IS NULL AND featured = true")),
    )


# ─────────────────────────────────────────────
#  Junction tables
# ─────────────────────────────────────────────

class EventTopic(Base):
    __tablename__ = "event_topics"

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True
    )


class EventGrade(Base):
    __tablename__ = "event_grades"

    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    grade_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("grades.id", ondelete="CASCADE"), primary_key=True
    )


class LessonEvent(Base):
    __tablename__ = "lesson_events"

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), primary_key=True
    )
    event_order: Mapped[int] = mapped_column(Integer, nullable=False)


# ─────────────────────────────────────────────
#  source_documents
# ─────────────────────────────────────────────

class SourceDocument(Base):
    __tablename__ = "source_documents"

    id: Mapped[uuid.UUID] = _uuid_pk()
    title: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'sgk'"))
    grade_hint: Mapped[str | None] = mapped_column(Text)
    era_hint: Mapped[str | None] = mapped_column(Text)
    storage_url: Mapped[str] = mapped_column(Text, nullable=False)
    checksum: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    mime_type: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'uploaded'"))
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = _now()
    processed_at: Mapped[datetime | None] = _nullable_ts()
    deleted_at: Mapped[datetime | None] = _nullable_ts()
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document")

    __table_args__ = (
        CheckConstraint(
            "source_type IN ('sgk','reference','other')",
            name="source_docs_type_check",
        ),
        CheckConstraint(
            "mime_type IN ('text/markdown','text/plain')",
            name="source_docs_mime_check",
        ),
        CheckConstraint("size_bytes > 0", name="source_docs_size_check"),
        CheckConstraint(
            "status IN ('uploaded','chunked','embedded','failed')",
            name="source_docs_status_check",
        ),
    )


# ─────────────────────────────────────────────
#  event_sources
# ─────────────────────────────────────────────

class EventSource(Base):
    __tablename__ = "event_sources"

    id: Mapped[uuid.UUID] = _uuid_pk()
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(
        String(30), nullable=False, server_default=text("'primary_source'")
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = _now()
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    document: Mapped[SourceDocument] = relationship()

    __table_args__ = (
        UniqueConstraint("event_id", "source_document_id", name="event_sources_unique"),
        CheckConstraint(
            "relation_type IN ('primary_source','secondary_source','reference','teacher_note')",
            name="event_sources_relation_check",
        ),
        Index("idx_event_sources_event", "event_id", "priority", "relation_type"),
    )


# ─────────────────────────────────────────────
#  document_chunks
# ─────────────────────────────────────────────

class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[uuid.UUID] = _uuid_pk()
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    section_title: Mapped[str | None] = mapped_column(Text)
    page_or_lesson_hint: Mapped[int | None] = mapped_column(Integer)
    chunk_metadata: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, server_default=text("'{}'"))
    created_at: Mapped[datetime] = _now()

    document: Mapped[SourceDocument] = relationship(back_populates="chunks")
    embedding: Mapped["ChunkEmbedding | None"] = relationship(back_populates="chunk")

    __table_args__ = (
        UniqueConstraint("document_id", "chunk_index", name="document_chunks_unique"),
        CheckConstraint("chunk_index >= 0", name="chunks_index_check"),
        CheckConstraint("token_count > 0", name="chunks_token_check"),
    )


# ─────────────────────────────────────────────
#  chunk_embeddings
# ─────────────────────────────────────────────

class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="CASCADE"), primary_key=True
    )
    embedding: Mapped[list[float]] = mapped_column(Vector(1024), nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    dim: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1024"))
    created_at: Mapped[datetime] = _now()

    chunk: Mapped[DocumentChunk] = relationship(back_populates="embedding")

    __table_args__ = (
        CheckConstraint("dim = 1024", name="embeddings_dim_check"),
    )


# ─────────────────────────────────────────────
#  event_story_versions
# ─────────────────────────────────────────────

class EventStoryVersion(Base):
    __tablename__ = "event_story_versions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    event_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("events.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    story_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'draft'"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = _now()
    published_at: Mapped[datetime | None] = _nullable_ts()
    notes: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = _nullable_ts()
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    event: Mapped[Event] = relationship(
        back_populates="story_versions",
        foreign_keys=[event_id],
    )
    citations: Mapped[list["BlockCitation"]] = relationship(back_populates="story_version")

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft','review','published','archived')",
            name="esv_status_check",
        ),
        CheckConstraint("version >= 1", name="esv_version_check"),
        # Only one published version per event
        Index(
            "idx_esv_one_published",
            "event_id",
            unique=True,
            postgresql_where=text("status = 'published' AND deleted_at IS NULL"),
        ),
    )


# ─────────────────────────────────────────────
#  block_citations
# ─────────────────────────────────────────────

class BlockCitation(Base):
    __tablename__ = "block_citations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    event_story_version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("event_story_versions.id", ondelete="CASCADE"), nullable=False
    )
    block_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="RESTRICT"), nullable=False
    )
    similarity: Mapped[float | None] = mapped_column(Numeric(4, 3))
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = _now()

    story_version: Mapped[EventStoryVersion] = relationship(back_populates="citations")
    chunk: Mapped[DocumentChunk] = relationship()

    __table_args__ = (
        UniqueConstraint(
            "event_story_version_id", "block_id", "chunk_id",
            name="block_citations_unique",
        ),
        CheckConstraint("similarity BETWEEN 0 AND 1", name="citations_similarity_check"),
        CheckConstraint("rank >= 1", name="citations_rank_check"),
        Index("idx_block_citations_version_block", "event_story_version_id", "block_id"),
    )


# ─────────────────────────────────────────────
#  image_assets
# ─────────────────────────────────────────────

class ImageAsset(Base):
    __tablename__ = "image_assets"

    id: Mapped[uuid.UUID] = _uuid_pk()
    storage_url: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    prompt: Mapped[str | None] = mapped_column(Text)
    model: Mapped[str | None] = mapped_column(Text)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))
    caption: Mapped[str | None] = mapped_column(Text)
    alt_text: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    created_at: Mapped[datetime] = _now()
    approved_at: Mapped[datetime | None] = _nullable_ts()
    approved_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    deleted_at: Mapped[datetime | None] = _nullable_ts()
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))

    __table_args__ = (
        CheckConstraint(
            "source IN ('ai_generated','admin_upload','stock')",
            name="image_assets_source_check",
        ),
        CheckConstraint(
            "status IN ('pending','approved','rejected')",
            name="image_assets_status_check",
        ),
    )


# ─────────────────────────────────────────────
#  generation_jobs
# ─────────────────────────────────────────────

class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("events.id"))
    event_story_version_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("event_story_versions.id")
    )
    image_asset_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("image_assets.id"))
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("source_documents.id"))
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'queued'"))
    input: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("3"))
    locked_by: Mapped[str | None] = mapped_column(Text)
    locked_at: Mapped[datetime | None] = _nullable_ts()
    queued_at: Mapped[datetime] = _now()
    started_at: Mapped[datetime | None] = _nullable_ts()
    finished_at: Mapped[datetime | None] = _nullable_ts()

    __table_args__ = (
        CheckConstraint(
            "type IN ('ingest','story_version','image')",
            name="jobs_type_check",
        ),
        CheckConstraint(
            "status IN ('queued','running','succeeded','failed','cancelled')",
            name="jobs_status_check",
        ),
        Index("idx_jobs_status", "status", "queued_at"),
        Index("idx_jobs_type_status", "type", "status"),
        Index(
            "idx_jobs_locked_at",
            "locked_at",
            postgresql_where=text("status = 'running'"),
        ),
    )


# ─────────────────────────────────────────────
#  review_items
# ─────────────────────────────────────────────

class ReviewItem(Base):
    __tablename__ = "review_items"

    id: Mapped[uuid.UUID] = _uuid_pk()
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)
    review_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = _now()
    reviewed_at: Mapped[datetime | None] = _nullable_ts()

    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('story_version','story_block','image_asset','comic_scene','slide_page')",
            name="review_entity_type_check",
        ),
        CheckConstraint(
            "review_type IN ('content_accuracy','image_quality','citation_check','publish_approval')",
            name="review_type_check",
        ),
        CheckConstraint(
            "status IN ('pending','approved','rejected')",
            name="review_status_check",
        ),
        Index("idx_review_items_status", "status", "created_at"),
        Index("idx_review_items_entity", "entity_type", "entity_id"),
    )


# ─────────────────────────────────────────────
#  audit_log
# ─────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = _uuid_pk()
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    action: Mapped[str] = mapped_column(Text, nullable=False)
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    diff: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = _now()

    __table_args__ = (
        Index("idx_audit_log_entity", "entity_type", "entity_id", "created_at"),
        Index("idx_audit_log_actor", "actor_id", "created_at"),
    )
