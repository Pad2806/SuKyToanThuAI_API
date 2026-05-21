revision = "003_ai_workspace_status"
down_revision = "002_auth_profile_credentials"
branch_labels = None
depends_on = None


from alembic import op


OLD_STATUSES = "'queued','pending','moderation_queued','rejected','processing','generating','generated','completed','failed','no_data','archived'"
NEW_STATUSES = "'queued','pending','moderation_queued','rejected','processing','needs_user_confirmation','generating','generated','completed','failed','no_data','archived'"


def upgrade() -> None:
    op.execute("ALTER TABLE public.user_pages DROP CONSTRAINT IF EXISTS user_pages_status_check")
    op.execute(
        f"""
        ALTER TABLE public.user_pages
        ADD CONSTRAINT user_pages_status_check
        CHECK (status IN ({NEW_STATUSES}))
        """
    )


def downgrade() -> None:
    op.execute("UPDATE public.user_pages SET status = 'pending' WHERE status = 'needs_user_confirmation'")
    op.execute("ALTER TABLE public.user_pages DROP CONSTRAINT IF EXISTS user_pages_status_check")
    op.execute(
        f"""
        ALTER TABLE public.user_pages
        ADD CONSTRAINT user_pages_status_check
        CHECK (status IN ({OLD_STATUSES}))
        """
    )
