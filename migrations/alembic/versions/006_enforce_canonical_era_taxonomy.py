from alembic import op

revision = "006_canonical_era_taxonomy"
down_revision = "005_replace_era_taxonomy"
branch_labels = None
depends_on = None

CANONICAL_ERA_IDS = (
    "era-tien-su-hong-bang",
    "era-cac-vua-hung",
    "era-au-lac",
    "era-bac-thuoc",
    "era-ngo",
    "era-dinh",
    "era-tien-le",
    "era-ly",
    "era-tran",
    "era-ho-minh-thuoc",
    "era-hau-le",
    "era-mac",
    "era-le-trung-hung",
    "era-tay-son",
    "era-nguyen",
    "era-phap-thuoc",
    "era-khang-chien-chong-phap",
    "era-khang-chien-chong-my",
    "era-viet-nam-hien-dai",
)


def upgrade() -> None:
    canonical_ids = ", ".join(f"'{era_id}'" for era_id in CANONICAL_ERA_IDS)
    op.execute(
        """
        UPDATE public.events
        SET era_id = 'era-tran', era_slug = 'tran', updated_at = now()
        WHERE era_id = 'era-dai-viet' OR era_slug = 'nha-tran'
        """
    )
    op.execute(
        f"""
        DO $$
        DECLARE
          bad_era_ids text;
        BEGIN
          SELECT string_agg(DISTINCT e.era_id, ', ' ORDER BY e.era_id)
          INTO bad_era_ids
          FROM public.events e
          WHERE e.era_id NOT IN ({canonical_ids});

          IF bad_era_ids IS NOT NULL THEN
            RAISE EXCEPTION 'Events still reference non-canonical eras: %', bad_era_ids;
          END IF;
        END $$;
        """
    )
    op.execute(
        f"""
        DELETE FROM public.eras
        WHERE id NOT IN ({canonical_ids})
        """
    )


def downgrade() -> None:
    pass
