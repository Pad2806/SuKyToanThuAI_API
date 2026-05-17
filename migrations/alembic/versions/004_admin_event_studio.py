from alembic import op

revision = "004_admin_event_studio"
down_revision = "003_ai_workspace_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE public.events ALTER COLUMN published_at DROP NOT NULL")
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS public.admin_event_asset_slots (
          id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
          event_id text NOT NULL REFERENCES public.events(id) ON DELETE CASCADE,
          story_version_id uuid REFERENCES public.event_story_versions(id) ON DELETE SET NULL,
          slot_key text NOT NULL,
          slot_label text NOT NULL,
          status text NOT NULL DEFAULT 'missing',
          prompt text,
          image_url text,
          gcs_uri text,
          review_notes text,
          metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
          approved_by uuid,
          approved_at timestamptz,
          created_at timestamptz NOT NULL DEFAULT now(),
          updated_at timestamptz NOT NULL DEFAULT now(),
          UNIQUE (event_id, slot_key),
          CONSTRAINT admin_event_asset_slots_status_check CHECK (
            status IN (
              'missing','prompted','queued','generated','approved',
              'rejected','failed','archived'
            )
          )
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_admin_event_asset_slots_event
        ON public.admin_event_asset_slots(event_id)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS public.admin_event_asset_slots")
    op.execute("UPDATE public.events SET published_at = now() WHERE published_at IS NULL")
    op.execute("ALTER TABLE public.events ALTER COLUMN published_at SET NOT NULL")
