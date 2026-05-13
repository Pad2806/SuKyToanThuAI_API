"""005_events_base

Create events table WITHOUT the FK to event_story_versions
(that FK is added in migration 013 after story versions table exists).

Revision ID: 005
Revises: 004
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("era_id", UUID(as_uuid=True), sa.ForeignKey("eras.id")),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("start_year", sa.Integer),
        sa.Column("end_year", sa.Integer),
        sa.Column("type", sa.String(30), nullable=False, server_default="other"),
        sa.Column("featured", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("excerpt", sa.Text, nullable=False),
        sa.Column("image", sa.Text, nullable=False),
        sa.Column("fallback_image", sa.Text),
        sa.Column("location", sa.Text),
        sa.Column("actors", ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("grade_tags", ARRAY(sa.Text), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("interactive_data", JSONB, nullable=False, server_default="{}"),
        sa.Column("template_type", sa.String(30), nullable=False, server_default="universal"),
        # published_story_version_id added in migration 013
        sa.Column("normalized_title", sa.Text, nullable=False, server_default=""),
        sa.Column("normalized_summary", sa.Text, nullable=False, server_default=""),
        sa.Column("normalized_search_text", sa.Text, nullable=False, server_default=""),
        sa.Column("published_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("deleted_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "type IN ('battle','dynasty','movement','culture','diplomacy','other')",
            name="events_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('draft','review','published','archived')",
            name="events_status_check",
        ),
        sa.CheckConstraint(
            "template_type IN ('universal','battle','dynasty','movement','culture','diplomacy')",
            name="events_template_check",
        ),
        sa.CheckConstraint(
            "(start_year IS NULL AND end_year IS NULL) OR "
            "(start_year IS NOT NULL AND end_year IS NOT NULL AND end_year >= start_year)",
            name="events_year_range_check",
        ),
    )

    # ── Indexes ──────────────────────────────────────────────────────────
    op.create_index(
        "idx_events_slug_active", "events", ["slug"],
        unique=True, postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_events_era_id", "events", ["era_id"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_events_year", "events", ["year"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_events_status", "events", ["status"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_events_featured", "events", ["featured"],
        postgresql_where=sa.text("deleted_at IS NULL AND featured = true"),
    )
    # GIN array indexes
    op.create_index(
        "idx_events_grade_tags", "events", ["grade_tags"],
        postgresql_using="gin",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_events_actors", "events", ["actors"],
        postgresql_using="gin",
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    for idx in [
        "idx_events_actors",
        "idx_events_grade_tags",
        "idx_events_featured",
        "idx_events_status",
        "idx_events_year",
        "idx_events_era_id",
        "idx_events_slug_active",
    ]:
        op.drop_index(idx)
    op.drop_table("events")
