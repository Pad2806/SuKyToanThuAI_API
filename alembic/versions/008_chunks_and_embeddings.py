"""008_document_chunks_and_embeddings

Create document_chunks and chunk_embeddings tables.
chunk_embeddings uses vector(1024) + HNSW index.

Revision ID: 008
Revises: 007
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("document_id", UUID(as_uuid=True),
                  sa.ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("chunk_index", sa.Integer, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("token_count", sa.Integer, nullable=False),
        sa.Column("section_title", sa.Text),
        sa.Column("page_or_lesson_hint", sa.Integer),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("document_id", "chunk_index", name="document_chunks_unique"),
        sa.CheckConstraint("chunk_index >= 0", name="chunks_index_check"),
        sa.CheckConstraint("token_count > 0", name="chunks_token_check"),
    )

    op.create_table(
        "chunk_embeddings",
        sa.Column("chunk_id", UUID(as_uuid=True),
                  sa.ForeignKey("document_chunks.id", ondelete="CASCADE"), primary_key=True),
        # vector(1024) via raw SQL — pgvector type not in core SQLAlchemy
        sa.Column("model", sa.Text, nullable=False),
        sa.Column("dim", sa.Integer, nullable=False, server_default="1024"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.CheckConstraint("dim = 1024", name="embeddings_dim_check"),
    )

    # Add vector column (pgvector type requires raw DDL)
    op.execute("ALTER TABLE chunk_embeddings ADD COLUMN embedding vector(1024) NOT NULL")

    # HNSW index for approximate nearest neighbor cosine search
    op.execute(
        "CREATE INDEX idx_chunk_embeddings_hnsw ON chunk_embeddings "
        "USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_chunk_embeddings_hnsw")
    op.drop_table("chunk_embeddings")
    op.drop_table("document_chunks")
