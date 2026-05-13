"""006_junction_tables

Create junction tables: event_topics, event_grades, lesson_events.

Revision ID: 006
Revises: 005
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_topics",
        sa.Column("event_id", UUID(as_uuid=True),
                  sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("topic_id", UUID(as_uuid=True),
                  sa.ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "event_grades",
        sa.Column("event_id", UUID(as_uuid=True),
                  sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("grade_id", UUID(as_uuid=True),
                  sa.ForeignKey("grades.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "lesson_events",
        sa.Column("lesson_id", UUID(as_uuid=True),
                  sa.ForeignKey("lessons.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("event_id", UUID(as_uuid=True),
                  sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("event_order", sa.Integer, nullable=False),
    )


def downgrade() -> None:
    op.drop_table("lesson_events")
    op.drop_table("event_grades")
    op.drop_table("event_topics")
