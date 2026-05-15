from uuid import UUID

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY, UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from common.db.base import Base


class OfficialTextUnit(Base):
    __tablename__ = "official_text_units"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    body: Mapped[str] = mapped_column(String)
    event_slugs: Mapped[list[str]] = mapped_column(ARRAY(String))


class RagSourceDocument(Base):
    __tablename__ = "rag_source_documents"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    title: Mapped[str] = mapped_column(String)


class RagDocumentChunk(Base):
    __tablename__ = "rag_document_chunks"

    id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True), primary_key=True)
    document_id: Mapped[UUID] = mapped_column(PgUUID(as_uuid=True))
    content: Mapped[str] = mapped_column(String)

