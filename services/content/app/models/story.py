from uuid import UUID

from sqlalchemy import Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from common.db.base import Base


class EventStoryVersion(Base):
    __tablename__ = "event_story_versions"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    event_id: Mapped[str] = mapped_column(String)
    version_number: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String)
    story_json: Mapped[dict] = mapped_column(JSONB)

