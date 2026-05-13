"""001_enable_extensions

Enable PostgreSQL extensions required by the system:
  - pgcrypto: gen_random_uuid()
  - vector:   pgvector for 1024-dim embeddings
  - pg_trgm:  trigram index for accent-insensitive search
  - unaccent: used by normalize function

Revision ID: 001
Revises: —
"""
from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE EXTENSION IF NOT EXISTS unaccent")


def downgrade() -> None:
    # Extensions are shared — downgrade is a no-op in most environments
    pass
