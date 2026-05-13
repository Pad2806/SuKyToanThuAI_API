"""003_users

Create users table.

Revision ID: 003
Revises: 002
"""
# pyrefly: ignore [missing-import]
import sqlalchemy as sa
from alembic import op
# pyrefly: ignore [missing-import]
from sqlalchemy.dialects.postgresql import UUID

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.Text, unique=True, nullable=False),
        sa.Column("password_hash", sa.Text, nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("display_name", sa.Text, nullable=False),
        sa.Column("active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True)),
        sa.CheckConstraint("role IN ('admin','editor','viewer')", name="users_role_check"),
    )


def downgrade() -> None:
    op.drop_table("users")
