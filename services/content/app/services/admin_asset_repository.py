import json
from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def list_asset_slots(db: AsyncSession, event_id: str) -> list[dict[str, Any]]:
    result = await db.execute(
        text(
            """
            SELECT * FROM public.admin_event_asset_slots
            WHERE event_id = :event_id AND status != 'archived'
            ORDER BY slot_key
            """
        ),
        {"event_id": event_id},
    )
    return [dict(row) for row in result.mappings().all()]


async def get_asset_slot(db: AsyncSession, event_id: str, slot_id: UUID) -> dict[str, Any] | None:
    result = await db.execute(
        text("SELECT * FROM public.admin_event_asset_slots WHERE id = :slot_id AND event_id = :event_id"),
        {"slot_id": slot_id, "event_id": event_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def upsert_asset_slot(db: AsyncSession, event_id: str, data: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "slot_key": data["slot_key"],
        "slot_label": data["slot_label"],
        "status": data.get("status") or "missing",
        "prompt": data.get("prompt"),
        "image_url": data.get("image_url"),
        "gcs_uri": data.get("gcs_uri"),
        "review_notes": data.get("review_notes"),
        "metadata": json.dumps(data.get("metadata") or {}),
    }
    result = await db.execute(
        text(
            """
            INSERT INTO public.admin_event_asset_slots
              (event_id, slot_key, slot_label, status, prompt, image_url, gcs_uri, review_notes, metadata)
            VALUES (:event_id, :slot_key, :slot_label, :status, :prompt, :image_url,
              :gcs_uri, :review_notes, CAST(:metadata AS jsonb))
            ON CONFLICT (event_id, slot_key) DO UPDATE SET
              slot_label = EXCLUDED.slot_label,
              status = CASE
                WHEN admin_event_asset_slots.status = 'approved' THEN admin_event_asset_slots.status
                ELSE EXCLUDED.status
              END,
              prompt = COALESCE(EXCLUDED.prompt, admin_event_asset_slots.prompt),
              image_url = CASE
                WHEN admin_event_asset_slots.status = 'approved' THEN admin_event_asset_slots.image_url
                ELSE EXCLUDED.image_url
              END,
              gcs_uri = COALESCE(EXCLUDED.gcs_uri, admin_event_asset_slots.gcs_uri),
              review_notes = EXCLUDED.review_notes,
              metadata = EXCLUDED.metadata, updated_at = now()
            RETURNING *
            """
        ),
        {"event_id": event_id, **payload},
    )
    return dict(result.mappings().one())


async def update_asset_slot(
    db: AsyncSession,
    event_id: str,
    slot_id: UUID,
    data: dict[str, Any],
) -> dict[str, Any]:
    current = await get_asset_slot(db, event_id, slot_id)
    if current is None:
        raise ValueError("Asset slot not found")
    if current["status"] == "approved" and data.get("image_url") != current.get("image_url"):
        raise ValueError("Approved assets cannot be overwritten")
    updates = {key: value for key, value in data.items() if value is not None}
    if not updates:
        return current
    assignments = ", ".join(f"{key} = :{key}" for key in updates)
    result = await db.execute(
        text(
            f"""
            UPDATE public.admin_event_asset_slots
            SET {assignments}, updated_at = now()
            WHERE id = :slot_id AND event_id = :event_id
            RETURNING *
            """
        ),
        {"event_id": event_id, "slot_id": slot_id, **updates},
    )
    return dict(result.mappings().one())


async def review_asset_slot(
    db: AsyncSession,
    slot_id: UUID,
    event_id: str,
    status: str,
    notes: str | None,
    admin_id: UUID,
) -> dict[str, Any]:
    approved = ", approved_by = :admin_id, approved_at = now()" if status == "approved" else ""
    result = await db.execute(
        text(
            f"""
            UPDATE public.admin_event_asset_slots
            SET status = :status, review_notes = :notes, updated_at = now(){approved}
            WHERE id = :slot_id AND event_id = :event_id
            RETURNING *
            """
        ),
        {"slot_id": slot_id, "event_id": event_id, "status": status, "notes": notes, "admin_id": admin_id},
    )
    row = result.mappings().first()
    if row is None:
        raise ValueError("Asset slot not found")
    return dict(row)
