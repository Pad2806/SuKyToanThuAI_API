from alembic import op

revision = "002_auth_profile_credentials"
down_revision = "001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS email text")
    op.execute("ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS hashed_password text")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_profiles_email ON public.profiles(email)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS public.idx_profiles_email")
    op.execute("ALTER TABLE public.profiles DROP COLUMN IF EXISTS hashed_password")
    op.execute("ALTER TABLE public.profiles DROP COLUMN IF EXISTS email")

