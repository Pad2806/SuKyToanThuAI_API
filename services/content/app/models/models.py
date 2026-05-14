"""Content Service — models: eras, grades, topics, lessons, events + junctions."""
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text,
    UniqueConstraint, func, text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from shared.core.database import Base


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))

def _now() -> Mapped[datetime]:
    return mapped_column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

def _nullable_ts() -> Mapped[datetime | None]:
    return mapped_column(TIMESTAMP(timezone=True), nullable=True)


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


class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = _uuid_pk()
    slug: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    cover_image: Mapped[str | None] = mapped_column(Text)


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
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    grade: Mapped[Grade] = relationship()

    __table_args__ = (
        Index("idx_lessons_grade_order", "grade_id", "lesson_order",
              postgresql_where=text("deleted_at IS NULL")),
    )


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
    # FK to story version — resolved via story-service HTTP call, not DB join
    published_story_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    normalized_title: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    normalized_summary: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    normalized_search_text: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    published_at: Mapped[datetime | None] = _nullable_ts()
    created_at: Mapped[datetime] = _now()
    updated_at: Mapped[datetime] = _now()
    deleted_at: Mapped[datetime | None] = _nullable_ts()
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))

    era: Mapped[Era | None] = relationship(back_populates="events")

    __table_args__ = (
        CheckConstraint("type IN ('battle','dynasty','movement','culture','diplomacy','other')", name="events_type_check"),
        CheckConstraint("status IN ('draft','review','published','archived')", name="events_status_check"),
        CheckConstraint("template_type IN ('universal','battle','dynasty','movement','culture','diplomacy')", name="events_template_check"),
        Index("idx_events_slug_active", "slug", unique=True, postgresql_where=text("deleted_at IS NULL")),
        Index("idx_events_era_id", "era_id", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_events_year", "year", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_events_status", "status", postgresql_where=text("deleted_at IS NULL")),
        Index("idx_events_featured", "featured", postgresql_where=text("deleted_at IS NULL AND featured = true")),
    )


# ─── Junction tables ─────────────────────────────────────────────────────────

class EventTopic(Base):
    __tablename__ = "event_topics"
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    topic_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)


class EventGrade(Base):
    __tablename__ = "event_grades"
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    grade_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("grades.id", ondelete="CASCADE"), primary_key=True)


class LessonEvent(Base):
    __tablename__ = "lesson_events"
    lesson_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True)
    event_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    event_order: Mapped[int] = mapped_column(Integer, nullable=False)
