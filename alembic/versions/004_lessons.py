"""004_lessons

Create lessons table (depends on grades + users).

Revision ID: 004
Revises: 003
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lessons",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("grade_id", UUID(as_uuid=True),
                  sa.ForeignKey("grades.id"), nullable=False),
        sa.Column("slug", sa.Text, nullable=False),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("lesson_order", sa.Integer, nullable=False),
        sa.Column("part", sa.Text),
        sa.Column("chapter", sa.Text),
        sa.Column("summary", sa.Text),
        sa.Column("cover_image", sa.Text),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("deleted_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
    )

    # Partial unique: unique(grade_id, slug) where deleted_at is null
    op.create_index(
        "idx_lessons_slug_active",
        "lessons",
        ["grade_id", "slug"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "idx_lessons_grade_order",
        "lessons",
        ["grade_id", "lesson_order"],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("idx_lessons_grade_order")
    op.drop_index("idx_lessons_slug_active")
    op.drop_table("lessons")
