from pathlib import Path

from alembic import op

revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    schema_path = _find_schema_file()
    op.execute(schema_path.read_text(encoding="utf-8"))


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS public.event_detail_api CASCADE")
    op.execute("DROP FUNCTION IF EXISTS public.get_story_event(text) CASCADE")
    op.execute("DROP FUNCTION IF EXISTS public.touch_updated_at() CASCADE")
    tables = [
        "model_usage_logs",
        "generation_job_steps",
        "generation_jobs",
        "user_page_assets",
        "user_page_moderation_results",
        "user_page_sources",
        "user_page_versions",
        "user_pages",
        "generation_requests",
        "page_templates",
        "rag_chunk_embeddings",
        "rag_document_chunks",
        "rag_source_documents",
        "official_text_units",
        "seed_sources",
        "story_image_assets",
        "story_block_citations",
        "event_story_versions",
        "story_templates",
        "profiles",
        "textbook_lessons",
        "textbook_parts",
        "event_grades",
        "events",
        "grades",
        "eras",
    ]
    for table in tables:
        op.execute(f"DROP TABLE IF EXISTS public.{table} CASCADE")


def _find_schema_file() -> Path:
    docker_schema = Path("/app/schema/sukyai-standard-schema.sql")
    if docker_schema.exists():
        return docker_schema

    for parent in Path(__file__).resolve().parents:
        candidate = parent / "docs" / "sukyai-standard-schema.sql"
        if candidate.exists():
            return candidate
    raise FileNotFoundError("docs/sukyai-standard-schema.sql was not found")
