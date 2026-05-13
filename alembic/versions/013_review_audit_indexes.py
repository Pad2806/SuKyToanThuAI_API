"""013_review_items_and_audit_log

Create review_items and audit_log tables.
Also adds the normalized_search_text trigram GIN index on events.

Revision ID: 013
Revises: 012
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── review_items ────────────────────────────────────────────────────
    op.create_table(
        "review_items",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("entity_id", sa.Text, nullable=False),
        sa.Column("review_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="'pending'"),
        sa.Column("reviewer_notes", sa.Text),
        sa.Column("created_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("reviewed_by", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
        sa.Column("reviewed_at", sa.TIMESTAMP(timezone=True)),
        sa.CheckConstraint(
            "entity_type IN ('story_version','story_block','image_asset','comic_scene','slide_page')",
            name="review_entity_type_check",
        ),
        sa.CheckConstraint(
            "review_type IN ('content_accuracy','image_quality','citation_check','publish_approval')",
            name="review_type_check",
        ),
        sa.CheckConstraint(
            "status IN ('pending','approved','rejected')",
            name="review_status_check",
        ),
    )

    op.create_index("idx_review_items_status", "review_items", ["status", "created_at"])
    op.create_index("idx_review_items_entity", "review_items", ["entity_type", "entity_id"])

    # ── audit_log ───────────────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("users.id")),
        sa.Column("action", sa.Text, nullable=False),
        sa.Column("entity_type", sa.Text, nullable=False),
        sa.Column("entity_id", UUID(as_uuid=True), nullable=False),
        sa.Column("diff", JSONB),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  nullable=False, server_default=sa.text("now()")),
    )

    op.create_index("idx_audit_log_entity", "audit_log",
                    ["entity_type", "entity_id", "created_at"])
    op.create_index("idx_audit_log_actor", "audit_log", ["actor_id", "created_at"])

    # ── Vietnamese trigram search index on events ────────────────────────
    op.create_index(
        "idx_events_normalized_search",
        "events",
        ["normalized_search_text"],
        postgresql_using="gin",
        postgresql_ops={"normalized_search_text": "gin_trgm_ops"},
        postgresql_where=sa.text("deleted_at IS NULL"),
    )

    # ── Trigger: prevent editing story_json of published versions ────────
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_published_story_edit()
        RETURNS TRIGGER LANGUAGE plpgsql AS $$
        BEGIN
            IF OLD.status = 'published'
               AND NEW.story_json IS DISTINCT FROM OLD.story_json THEN
                RAISE EXCEPTION
                    'Cannot edit story_json of a published event_story_version (id=%)', OLD.id;
            END IF;
            RETURN NEW;
        END;
        $$;
    """)

    op.execute("""
        CREATE TRIGGER trg_prevent_published_story_edit
        BEFORE UPDATE ON event_story_versions
        FOR EACH ROW EXECUTE FUNCTION prevent_published_story_edit();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_prevent_published_story_edit ON event_story_versions")
    op.execute("DROP FUNCTION IF EXISTS prevent_published_story_edit()")
    op.drop_index("idx_events_normalized_search")
    op.drop_index("idx_audit_log_actor")
    op.drop_index("idx_audit_log_entity")
    op.drop_table("audit_log")
    op.drop_index("idx_review_items_entity")
    op.drop_index("idx_review_items_status")
    op.drop_table("review_items")
