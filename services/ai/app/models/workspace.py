from uuid import UUID

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from common.db.base import Base


class UserPage(Base):
    __tablename__ = "user_pages"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    user_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    title: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)


class UserPageVersion(Base):
    __tablename__ = "user_page_versions"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    page_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    render_payload: Mapped[dict] = mapped_column(JSONB)

