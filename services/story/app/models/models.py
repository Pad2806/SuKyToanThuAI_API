"""Story Service — models: event_story_versions, block_citations, image_assets, review_items."""
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint, Index, Integer, Numeric, String, Text,
    UniqueConstraint, func, text,
)
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.core.database import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

def _now() -> Mapped[datetime]:
    return mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

def _nullable_ts() -> Mapped[datetime | None]:
    return mapped_column(TIMESTAMP(timezone=True), nullable=True)


class EventStoryVersion(Base):
    __tablename__ = "event_story_versions"

    id: Mapped[uuid.UUID] = _uuid_pk()
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    story_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'draft'"))
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = _now()
    published_at: Mapped[datetime | None] = _nullable_ts()
    notes: Mapped[str | None] = mapped_column(Text)
    deleted_at: Mapped[datetime | None] = _nullable_ts()
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    citations: Mapped[list["BlockCitation"]] = relationship(back_populates="story_version")

    __table_args__ = (
        CheckConstraint("status IN ('draft','review','published','archived')", name="esv_status_check"),
        CheckConstraint("version >= 1", name="esv_version_check"),
        Index("idx_esv_one_published", "event_id", unique=True,
              postgresql_where=text("status = 'published' AND deleted_at IS NULL")),
    )


class BlockCitation(Base):
    __tablename__ = "block_citations"

    id: Mapped[uuid.UUID] = _uuid_pk()
    event_story_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    block_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    similarity: Mapped[float | None] = mapped_column(Numeric(4, 3))
    rank: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = _now()

    story_version: Mapped[EventStoryVersion] = relationship(back_populates="citations")

    __table_args__ = (
        UniqueConstraint("event_story_version_id", "block_id", "chunk_id", name="block_citations_unique"),
        CheckConstraint("similarity BETWEEN 0 AND 1", name="citations_similarity_check"),
        CheckConstraint("rank >= 1", name="citations_rank_check"),
        Index("idx_block_citations_version_block", "event_story_version_id", "block_id"),
    )


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
    approved_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    deleted_at: Mapped[datetime | None] = _nullable_ts()
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    __table_args__ = (
        CheckConstraint("source IN ('ai_generated','admin_upload','stock')", name="image_assets_source_check"),
        CheckConstraint("status IN ('pending','approved','rejected')", name="image_assets_status_check"),
    )


class ReviewItem(Base):
    __tablename__ = "review_items"

    id: Mapped[uuid.UUID] = _uuid_pk()
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)
    review_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default=text("'pending'"))
    reviewer_notes: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
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
        CheckConstraint("status IN ('pending','approved','rejected')", name="review_status_check"),
        Index("idx_review_items_status", "status", "created_at"),
        Index("idx_review_items_entity", "entity_type", "entity_id"),
    )
