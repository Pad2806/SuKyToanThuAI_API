import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import admin_asset_repository as assets
from app.services import admin_event_repository as events
from app.services.event_quality_gate import validate_event_quality


async def quality_report(db: AsyncSession, event_id: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    event = await events.get_event(db, event_id)
    if event is None:
        raise ValueError("Event not found")
    story = await events.get_latest_story(db, event["id"])
    slot_rows = await assets.list_asset_slots(db, event["id"])
    return validate_event_quality(
        event,
        story["story_json"] if story else None,
        slot_rows,
        sources,
        story.get("generation_metadata") if story else None,
    )


async def submit_review(db: AsyncSession, event_id: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    event = await events.get_event(db, event_id)
    if event is None:
        raise ValueError("Event not found")
    story = await events.get_latest_story(db, event["id"])
    if story is None:
        raise ValueError("Story draft is required")
    report = validate_event_quality(
        event,
        story["story_json"],
        await assets.list_asset_slots(db, event["id"]),
        sources,
        story.get("generation_metadata") or {},
    )
    missing = [key for key in ("facts", "story", "sources", "citations") if not report["requirements"].get(key)]
    if missing:
        raise ValueError("Review requires complete facts, story, sources, and citations")
    await db.execute(text("UPDATE public.events SET status = 'review', updated_at = now() WHERE id = :id"), {"id": event["id"]})
    await db.execute(text("UPDATE public.event_story_versions SET status = 'review' WHERE id = :id"), {"id": story["id"]})
    return {"id": event["id"], "status": "review"}


async def publish(db: AsyncSession, event_id: str, sources: list[dict[str, Any]]) -> dict[str, Any]:
    event = await events.get_event(db, event_id)
    if event is None:
        raise ValueError("Event not found")
    story = await events.get_latest_story(db, event["id"])
    if story is None:
        raise ValueError("Story draft is required")
    slot_rows = await assets.list_asset_slots(db, event["id"])
    report = validate_event_quality(
        event,
        story["story_json"],
        slot_rows,
        sources,
        story.get("generation_metadata") or {},
    )
    if not report["passed"]:
        return {"status": "blocked", "quality": report}

    hero = next((slot for slot in slot_rows if slot["slot_key"] == "hero" and slot["status"] == "approved"), None)
    await db.execute(text("UPDATE public.event_story_versions SET status = 'archived' WHERE event_id = :event_id AND status = 'published'"), {"event_id": event["id"]})
    await db.execute(text("UPDATE public.event_story_versions SET status = 'published', published_at = now() WHERE id = :id"), {"id": story["id"]})
    await db.execute(
        text(
            """
            UPDATE public.events
            SET status = 'published', image = COALESCE(:image_url, image),
                published_at = now(), updated_at = now()
            WHERE id = :event_id
            """
        ),
        {"event_id": event["id"], "image_url": hero["image_url"] if hero else None},
    )
    await _copy_approved_assets(db, event["id"], story["id"], slot_rows)
    return {"status": "published", "quality": report}


async def archive(db: AsyncSession, event_id: str) -> dict[str, Any]:
    event = await events.get_event(db, event_id)
    if event is None:
        raise ValueError("Event not found")
    await db.execute(text("UPDATE public.events SET status = 'archived', updated_at = now() WHERE id = :id"), {"id": event["id"]})
    return {"id": event["id"], "status": "archived"}


async def _copy_approved_assets(db: AsyncSession, event_id: str, story_id, slot_rows: list[dict[str, Any]]) -> None:
    for slot in slot_rows:
        if slot["status"] != "approved" or not slot.get("image_url"):
            continue
        await db.execute(
            text(
                """
                INSERT INTO public.story_image_assets
                  (event_id, story_version_id, prompt, image_url, metadata)
                VALUES (:event_id, :story_id, :prompt, :image_url, CAST(:metadata AS jsonb))
                """
            ),
            {
                "event_id": event_id,
                "story_id": story_id,
                "prompt": slot.get("prompt"),
                "image_url": slot["image_url"],
                "metadata": json.dumps({"slot": slot["slot_key"], **(slot.get("metadata") or {})}),
            },
        )
