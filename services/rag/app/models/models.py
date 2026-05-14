"""RAG Service — models: source_documents, chunks, embeddings, event_sources."""
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger, CheckConstraint, ForeignKey, Index, Integer, String, Text,
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
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    uploaded_at: Mapped[datetime] = _now()
    processed_at: Mapped[datetime | None] = _nullable_ts()
    deleted_at: Mapped[datetime | None] = _nullable_ts()
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document")

    __table_args__ = (
        CheckConstraint("source_type IN ('sgk','reference','other')", name="source_docs_type_check"),
        # PDF added alongside markdown and plain text
        CheckConstraint(
            "mime_type IN ('text/markdown','text/plain','application/pdf')",
            name="source_docs_mime_check",
        ),
        CheckConstraint("size_bytes > 0", name="source_docs_size_check"),
        CheckConstraint("status IN ('uploaded','chunked','embedded','failed')", name="source_docs_status_check"),
    )


class EventSource(Base):
    """RAG truth-source: links an Event (by ID) to a SourceDocument."""
    __tablename__ = "event_sources"

    id: Mapped[uuid.UUID] = _uuid_pk()
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False
    )
    relation_type: Mapped[str] = mapped_column(String(30), nullable=False, server_default=text("'primary_source'"))
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    created_at: Mapped[datetime] = _now()
    created_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    document: Mapped[SourceDocument] = relationship()

    __table_args__ = (
        UniqueConstraint("event_id", "source_document_id", name="event_sources_unique"),
        CheckConstraint(
            "relation_type IN ('primary_source','secondary_source','reference','teacher_note')",
            name="event_sources_relation_check",
        ),
        Index("idx_event_sources_event", "event_id", "priority", "relation_type"),
    )


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
