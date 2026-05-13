"""010_image_assets

Create image_assets table.

Revision ID: 010
Revises: 009
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "image_assets",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("storage_url", sa.Text, nullable=False),
        sa.Column("thumbnail_url", sa.Text),
        sa.Column("source", sa.String(30), nullable=False),
        sa.Column("prompt", sa.Text),
        sa.Column("model", sa.Text),
        sa.Column("width", sa.Integer),
        sa.Column("height", sa.Integer),
        sa.Column("status", sa.String(20), nullable=False, server_default="'pending'"),
        sa.Column("caption", sa.Text),
        sa.Column("alt_text", sa.Text, nullable=False, server_default="''"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("approved_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("approved_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True)),
        sa.Column("deleted_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.CheckConstraint(
            "source IN ('ai_generated','admin_upload','stock')",
            name="image_assets_source_check",
        ),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected')",
            name="image_assets_status_check",
        ),
    )


def downgrade() -> None:
    op.drop_table("image_assets")
