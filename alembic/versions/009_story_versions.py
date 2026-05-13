"""009_event_story_versions

Create event_story_versions table and block_citations.

Revision ID: 009
Revises: 008
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_story_versions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_id", UUID(as_uuid=True),
                  sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column("story_json", JSONB, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'draft'"),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("notes", sa.Text),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("deleted_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "status IN ('draft','review','published','archived')",
            name="esv_status_check",
        ),
        sa.CheckConstraint("version >= 1", name="esv_version_check"),
    )

    # Only one published version per event at a time
    op.create_index(
        "idx_esv_one_published",
        "event_story_versions",
        ["event_id"],
        unique=True,
        postgresql_where=sa.text("status = 'published' AND deleted_at IS NULL"),
    )

    # block_citations
    op.create_table(
        "block_citations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("event_story_version_id", UUID(as_uuid=True),
                  sa.ForeignKey("event_story_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("block_id", UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_id", UUID(as_uuid=True),
                  sa.ForeignKey("document_chunks.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("similarity", sa.Numeric(4, 3)),
        sa.Column("rank", sa.Integer, nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "event_story_version_id", "block_id", "chunk_id",
            name="block_citations_unique",
        ),
        sa.CheckConstraint("similarity BETWEEN 0 AND 1", name="citations_similarity_check"),
        sa.CheckConstraint("rank >= 1", name="citations_rank_check"),
    )

    op.create_index(
        "idx_block_citations_version_block",
        "block_citations",
        ["event_story_version_id", "block_id"],
    )


def downgrade() -> None:
    op.drop_index("idx_block_citations_version_block")
    op.drop_table("block_citations")
    op.drop_index("idx_esv_one_published")
    op.drop_table("event_story_versions")
