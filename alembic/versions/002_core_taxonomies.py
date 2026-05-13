"""002_core_taxonomies

Create core taxonomy tables: eras, grades, topics.
These are the root entities with no foreign-key dependencies.

Revision ID: 002
Revises: 001
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── eras ────────────────────────────────────────────────────────────
    op.create_table(
        "eras",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.Text, unique=True, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("year_range", sa.Text, nullable=False),
        sa.Column("start_year", sa.Integer, nullable=False),
        sa.Column("end_year", sa.Integer, nullable=False),
        sa.Column("summary", sa.Text, nullable=False),
        sa.Column("cover_image", sa.Text, nullable=False),
        sa.Column("fallback_image", sa.Text),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("end_year >= start_year", name="eras_years_check"),
    )

    # ── grades ──────────────────────────────────────────────────────────
    op.create_table(
        "grades",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("level", sa.Integer, unique=True, nullable=False),
        sa.Column("slug", sa.Text, unique=True, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("order_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("level BETWEEN 5 AND 12", name="grades_level_check"),
    )

    # ── topics ──────────────────────────────────────────────────────────
    op.create_table(
        "topics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("slug", sa.Text, unique=True, nullable=False),
        sa.Column("name", sa.Text, nullable=False),
        sa.Column("description", sa.Text),
        sa.Column("cover_image", sa.Text),
    )


def downgrade() -> None:
    op.drop_table("topics")
    op.drop_table("grades")
    op.drop_table("eras")
