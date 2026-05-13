"""
PublishValidator — Application-layer guard for publishing event story versions.

Rules enforced here (NOT in DB triggers):
  1. Event must have at least one event_source.
  2. Story version must contain all required beat types.
  3. Every public-renderable block must have status='approved'.
  4. Every public-renderable block must have at least one block_citation.
  5. manual_required blocks must not be public-renderable (must be hidden/skipped).
  6. Any imageAssetId in a public block must point to image_assets.status='approved'.
  7. Only one published story version per event (enforced by DB unique index, also checked here).
  8. AI worker must never set featured=true (validated on ingest, not here).
"""
import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    BlockCitation,
    EventSource,
    EventStoryVersion,
    ImageAsset,
)

# Beat types required in every published story
REQUIRED_BEATS = {"hook", "setup", "rising", "climax", "falling", "takeaway"}

# Block statuses that can be shown publicly
PUBLIC_RENDERABLE_STATUSES = {"approved"}

# Block statuses that are explicitly non-public
NON_PUBLIC_STATUSES = {"manual_required", "rejected"}


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]


class PublishValidator:
    """Validate that a story version is ready to publish."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def validate(self, story_version_id: uuid.UUID) -> ValidationResult:
        errors: list[str] = []

        # Load story version
        version = await self.db.get(EventStoryVersion, story_version_id)
        if version is None:
            return ValidationResult(ok=False, errors=["Story version not found."])

        if version.deleted_at is not None:
            return ValidationResult(ok=False, errors=["Story version is soft-deleted."])

        # ── Rule 1: Event must have at least one event_source ────────────
        source_count = await self.db.scalar(
            select(func.count()).where(EventSource.event_id == version.event_id)
        )
        if not source_count:
            errors.append("Event has no event_sources. Attach at least one source document.")

        # ── Rule 7: No other published version for this event ────────────
        existing_published = await self.db.scalar(
            select(func.count()).where(
                EventStoryVersion.event_id == version.event_id,
                EventStoryVersion.status == "published",
                EventStoryVersion.deleted_at.is_(None),
                EventStoryVersion.id != story_version_id,
            )
        )
        if existing_published:
            errors.append("Another published version already exists for this event.")

        # ── Parse story_json ─────────────────────────────────────────────
        story_json: dict = version.story_json or {}
        beats: list[dict] = story_json.get("beats", [])

        # ── Rule 2: Required beats present ──────────────────────────────
        present_beat_types = {b.get("type", "").lower() for b in beats}
        missing_beats = REQUIRED_BEATS - present_beat_types
        if missing_beats:
            errors.append(f"Missing required beats: {', '.join(sorted(missing_beats))}")

        # ── Collect all public blocks ────────────────────────────────────
        public_block_ids: list[uuid.UUID] = []
        image_asset_ids: list[uuid.UUID] = []

        for beat in beats:
            for block in beat.get("blocks", []):
                block_status = block.get("status", "draft")
                block_id_str = block.get("id")

                # Rule 5: manual_required must not be in public story
                if block_status == "manual_required":
                    errors.append(
                        f"Block {block_id_str} has status='manual_required' "
                        "and must be replaced or hidden before publish."
                    )
                    continue

                # Only consider approved blocks for further checks
                if block_status not in PUBLIC_RENDERABLE_STATUSES:
                    # draft/rejected blocks in story_json are considered non-published
                    # PublishValidator rejects if ANY block is not approved or manual_required
                    errors.append(
                        f"Block {block_id_str} has status='{block_status}'. "
                        "All blocks must be approved before publishing."
                    )
                    continue

                # Rule 3: Block is approved → collect for citation check
                try:
                    block_uuid = uuid.UUID(block_id_str)
                    public_block_ids.append(block_uuid)
                except (TypeError, ValueError):
                    errors.append(f"Block has invalid UUID: {block_id_str}")
                    continue

                # Rule 6: imageAssetId must be approved
                image_asset_id_str = block.get("imageAssetId")
                if image_asset_id_str:
                    try:
                        image_asset_ids.append(uuid.UUID(image_asset_id_str))
                    except ValueError:
                        errors.append(f"Block {block_id_str} has invalid imageAssetId.")

        # ── Rule 4: Every public block must have at least 1 citation ─────
        if public_block_ids:
            cited_block_ids_result = await self.db.execute(
                select(BlockCitation.block_id)
                .where(BlockCitation.event_story_version_id == story_version_id)
                .where(BlockCitation.block_id.in_(public_block_ids))
                .distinct()
            )
            cited_block_ids = {row[0] for row in cited_block_ids_result.fetchall()}
            uncited = set(public_block_ids) - cited_block_ids
            if uncited:
                errors.append(
                    f"{len(uncited)} public block(s) have no citations: "
                    + ", ".join(str(b) for b in list(uncited)[:5])
                )

        # ── Rule 6: Check all referenced image assets are approved ───────
        if image_asset_ids:
            unapproved_result = await self.db.execute(
                select(ImageAsset.id).where(
                    ImageAsset.id.in_(image_asset_ids),
                    ImageAsset.status != "approved",
                    ImageAsset.deleted_at.is_(None),
                )
            )
            unapproved = unapproved_result.scalars().all()
            if unapproved:
                errors.append(
                    f"{len(unapproved)} image asset(s) are not approved: "
                    + ", ".join(str(i) for i in unapproved[:5])
                )

        return ValidationResult(ok=len(errors) == 0, errors=errors)
