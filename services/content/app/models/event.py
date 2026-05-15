from sqlalchemy import Boolean, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from common.db.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    slug: Mapped[str] = mapped_column(String, unique=True)
    title: Mapped[str] = mapped_column(String)
    era_id: Mapped[str] = mapped_column(String)
    era_slug: Mapped[str] = mapped_column(String)
    year: Mapped[int] = mapped_column(Integer)
    start_year: Mapped[int | None] = mapped_column(Integer)
    end_year: Mapped[int | None] = mapped_column(Integer)
    grade_tags: Mapped[list[str]] = mapped_column(ARRAY(String))
    type: Mapped[str] = mapped_column(String)
    featured: Mapped[bool] = mapped_column(Boolean)
    summary: Mapped[str] = mapped_column(String)
    excerpt: Mapped[str] = mapped_column(String)
    image: Mapped[str] = mapped_column(String)
    fallback_image: Mapped[str | None] = mapped_column(String)
    location: Mapped[str | None] = mapped_column(String)
    actors: Mapped[list[str]] = mapped_column(ARRAY(String))
    opponent: Mapped[str | None] = mapped_column(String)
    result: Mapped[str | None] = mapped_column(String)
    theme: Mapped[str] = mapped_column(String)
    template_type: Mapped[str] = mapped_column(String)
    related_event_slugs: Mapped[list[str]] = mapped_column(ARRAY(String))
    interactive_data: Mapped[dict] = mapped_column(JSONB)


class EventGrade(Base):
    __tablename__ = "event_grades"

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    grade_id: Mapped[str] = mapped_column(String, primary_key=True)

