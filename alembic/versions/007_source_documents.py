"""007_source_documents_and_event_sources

Create source_documents and event_sources tables.

Revision ID: 007
Revises: 006
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "007"
down_revision = "006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "source_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("source_type", sa.String(20), nullable=False, server_default="'sgk'"),
        sa.Column("grade_hint", sa.Text),
        sa.Column("era_hint", sa.Text),
        sa.Column("storage_url", sa.Text, nullable=False),
        sa.Column("checksum", sa.Text, unique=True, nullable=False),
        sa.Column("mime_type", sa.Text, nullable=False),
        sa.Column("size_bytes", sa.BigInteger, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'uploaded'"),
        sa.Column("uploaded_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("uploaded_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("processed_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("deleted_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "source_type IN ('sgk','reference','other')",
            name="source_docs_type_check",
        ),
        sa.CheckConstraint(
            "mime_type IN ('text/markdown','text/plain')",
            name="source_docs_mime_check",
        ),
        sa.CheckConstraint("size_bytes > 0", name="source_docs_size_check"),
        sa.CheckConstraint(
            "status IN ('uploaded','chunked','embedded','failed')",
            name="source_docs_status_check",
        ),
    )

    op.create_table(
        "event_sources",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_id", UUID(as_uuid=True),
                  sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_document_id", UUID(as_uuid=True),
                  sa.ForeignKey("source_documents.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("relation_type", sa.String(30), nullable=False,
                  server_default="'primary_source'"),
        sa.Column("priority", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.UniqueConstraint("event_id", "source_document_id", name="event_sources_unique"),
        sa.CheckConstraint(
            "relation_type IN ('primary_source','secondary_source','reference','teacher_note')",
            name="event_sources_relation_check",
        ),
    )

    op.create_index(
        "idx_event_sources_event",
        "event_sources",
        ["event_id", "priority", "relation_type"],
    )


def downgrade() -> None:
    op.drop_index("idx_event_sources_event")
    op.drop_table("event_sources")
    op.drop_table("source_documents")
