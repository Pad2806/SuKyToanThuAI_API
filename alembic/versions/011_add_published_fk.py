"""011_add_published_story_version_fk

Add FK events.published_story_version_id → event_story_versions.id
This deferred FK was withheld in 005 to avoid circular dependency.

Revision ID: 011
Revises: 010
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add column first, then FK constraint
    op.add_column(
        "events",
        sa.Column("published_story_version_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_events_published_version",
        "events",
        "event_story_versions",
        ["published_story_version_id"],
        ["id"],
        use_alter=True,
    )


def downgrade() -> None:
    op.drop_constraint("fk_events_published_version", "events", type_="foreignkey")
    op.drop_column("events", "published_story_version_id")
