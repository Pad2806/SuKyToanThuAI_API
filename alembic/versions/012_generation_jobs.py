"""012_generation_jobs

Create generation_jobs table for PostgreSQL-based queue.
Uses SELECT FOR UPDATE SKIP LOCKED — no Redis/Celery needed.

Revision ID: 012
Revises: 011
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "generation_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("event_id", UUID(as_uuid=True), sa.ForeignKey("events.id")),
        sa.Column("event_story_version_id", UUID(as_uuid=True),
                  sa.ForeignKey("event_story_versions.id")),
        sa.Column("image_asset_id", UUID(as_uuid=True), sa.ForeignKey("image_assets.id")),
        sa.Column("source_document_id", UUID(as_uuid=True),
                  sa.ForeignKey("source_documents.id")),
        sa.Column("status", sa.String(20), nullable=False, server_default="'queued'"),
        sa.Column("input", JSONB, nullable=False),
        sa.Column("output", JSONB),
        sa.Column("error", sa.Text),
        sa.Column("attempts", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="3"),
        sa.Column("locked_by", sa.Text),
        sa.Column("locked_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("queued_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("finished_at", sa.TIMESTAMP(timezone=True)),
        sa.CheckConstraint(
            "type IN ('ingest','story_version','image')",
            name="jobs_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('queued','running','succeeded','failed','cancelled')",
            name="jobs_status_check",
        ),
    )

    op.create_index("idx_jobs_status", "generation_jobs", ["status", "queued_at"])
    op.create_index("idx_jobs_type_status", "generation_jobs", ["type", "status"])
    op.create_index(
        "idx_jobs_locked_at",
        "generation_jobs",
        ["locked_at"],
        postgresql_where=sa.text("status = 'running'"),
    )


def downgrade() -> None:
    op.drop_index("idx_jobs_locked_at")
    op.drop_index("idx_jobs_type_status")
    op.drop_index("idx_jobs_status")
    op.drop_table("generation_jobs")
