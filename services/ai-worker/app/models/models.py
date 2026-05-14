"""AI Worker Service — model: generation_jobs."""
import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from shared.core.database import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

def _now() -> Mapped[datetime]:
    return mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

def _nullable_ts() -> Mapped[datetime | None]:
    return mapped_column(TIMESTAMP(timezone=True), nullable=True)


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id: Mapped[uuid.UUID] = _uuid_pk()
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    # All cross-service IDs stored as plain UUID columns (no FK across services)
    event_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    event_story_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    image_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
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
        CheckConstraint("type IN ('ingest','story_version','image')", name="jobs_type_check"),
        CheckConstraint("status IN ('queued','running','succeeded','failed','cancelled')", name="jobs_status_check"),
        Index("idx_jobs_status", "status", "queued_at"),
        Index("idx_jobs_type_status", "type", "status"),
        Index("idx_jobs_locked_at", "locked_at", postgresql_where=text("status = 'running'")),
    )
