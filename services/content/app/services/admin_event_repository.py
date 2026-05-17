import json
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

EVENT_COLUMNS = """
id, slug, title, era_id, era_slug, year, start_year, end_year, grade_tags,
type, featured, summary, excerpt, image, fallback_image, location, actors,
opponent, result, theme, template_type, related_event_slugs, status,
interactive_data, published_at, created_at, updated_at, deleted_at
"""


async def list_admin_events(db: AsyncSession, status: str | None) -> list[dict[str, Any]]:
    where = "deleted_at IS NULL"
    params: dict[str, Any] = {}
    if status:
        where += " AND status = :status"
        params["status"] = status
    result = await db.execute(
        text(f"SELECT {EVENT_COLUMNS} FROM public.events WHERE {where} ORDER BY updated_at DESC"),
        params,
    )
    return [dict(row) for row in result.mappings().all()]

async def list_admin_options(db: AsyncSession) -> dict[str, Any]:
    eras = await db.execute(
        text(
            """
            SELECT id, slug, name, year_range
            FROM public.eras
            ORDER BY order_index, start_year NULLS LAST, name
            """
        )
    )
    return {
        "eras": [dict(row) for row in eras.mappings().all()],
        "eventTypes": ["battle", "dynasty", "movement", "culture", "diplomacy", "other"],
        "templateTypes": ["universal", "battle", "dynasty", "movement", "culture", "diplomacy"],
    }


async def create_event(db: AsyncSession, data: dict[str, Any]) -> dict[str, Any]:
    era = await _require_era(db, data.get("era_id"), data.get("era_slug"))
    event_id = data.get("id") or f"event-{data['slug']}"
    summary = data.get("summary") or ""
    result = await db.execute(
        text(
            f"""
            INSERT INTO public.events (
              id, slug, title, era_id, era_slug, year, grade_tags, type, featured,
              summary, excerpt, image, fallback_image, actors, theme, template_type,
              related_event_slugs, status, interactive_data, published_at
            )
            VALUES (
              :id, :slug, :title, :era_id, :era_slug, :year, '{{}}', :type, false,
              :summary, :excerpt, '', '/images/generated/parchment.png', '{{}}',
              'vietnamese-history', :template_type, '{{}}', 'draft',
              CAST(:interactive_data AS jsonb), NULL
            )
            RETURNING {EVENT_COLUMNS}
            """
        ),
        {
            "id": event_id,
            "slug": data["slug"],
            "title": data["title"],
            "era_id": era["id"],
            "era_slug": era["slug"],
            "year": data.get("year") or 0,
            "type": data.get("type") or "other",
            "template_type": data.get("template_type") or "universal",
            "summary": summary,
            "excerpt": summary[:220],
            "interactive_data": json.dumps(_empty_interactions()),
        },
    )
    return dict(result.mappings().one())


async def get_event(db: AsyncSession, event_id: str) -> dict[str, Any] | None:
    result = await db.execute(
        text(
            f"""
            SELECT {EVENT_COLUMNS} FROM public.events
            WHERE (id = :event_id OR slug = :event_id) AND deleted_at IS NULL
            LIMIT 1
            """
        ),
        {"event_id": event_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def get_latest_story(db: AsyncSession, event_id: str) -> dict[str, Any] | None:
    result = await db.execute(
        text(
            """
            SELECT * FROM public.event_story_versions
            WHERE event_id = :event_id AND status != 'archived'
            ORDER BY
              CASE status WHEN 'draft' THEN 0 WHEN 'review' THEN 1 ELSE 2 END,
              version_number DESC
            LIMIT 1
            """
        ),
        {"event_id": event_id},
    )
    row = result.mappings().first()
    return dict(row) if row else None


async def update_facts(db: AsyncSession, event_id: str, data: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "title", "slug", "era_id", "era_slug", "year", "start_year", "end_year",
        "grade_tags", "type", "template_type", "summary", "excerpt", "image",
        "fallback_image", "location", "actors", "opponent", "result", "theme",
        "related_event_slugs",
    }
    updates = {key: value for key, value in data.items() if key in allowed and value is not None}
    if "era_id" in updates or "era_slug" in updates:
        era = await _require_era(db, updates.get("era_id"), updates.get("era_slug"))
        updates["era_id"] = era["id"]
        updates["era_slug"] = era["slug"]
    if "summary" in updates and "excerpt" not in updates:
        updates["excerpt"] = str(updates["summary"])[:220]
    if not updates:
        event = await get_event(db, event_id)
        if event is None:
            raise ValueError("Event not found")
        if event["status"] == "published":
            raise ValueError("Event not found or already published")
        return event
    assignments = ", ".join(f"{key} = :{key}" for key in updates)
    params = {"event_id": event_id, **updates}
    result = await db.execute(
        text(
            f"""
            UPDATE public.events
            SET {assignments}, updated_at = now()
            WHERE (id = :event_id OR slug = :event_id) AND status IN ('draft', 'review')
            RETURNING {EVENT_COLUMNS}
            """
        ),
        params,
    )
    row = result.mappings().first()
    if row is None:
        raise ValueError("Event not found or not editable")
    return dict(row)


async def upsert_story(
    db: AsyncSession,
    event_id: str,
    story: dict[str, Any],
    generation_metadata: dict[str, Any],
) -> dict[str, Any]:
    await _require_editable_event(db, event_id)
    existing = await get_latest_story(db, event_id)
    if existing and existing["status"] == "draft":
        result = await db.execute(
            text(
                """
                UPDATE public.event_story_versions
                SET story_json = CAST(:story AS jsonb),
                    generation_metadata = CAST(:metadata AS jsonb),
                    updated_at = now()
                WHERE id = :id
                RETURNING *
                """
            ),
            {"id": existing["id"], "story": json.dumps(story), "metadata": json.dumps(generation_metadata)},
        )
        return dict(result.mappings().one())

    version = await _next_story_version(db, event_id)
    result = await db.execute(
        text(
            """
            INSERT INTO public.event_story_versions
              (event_id, version_number, status, story_json, generation_metadata)
            VALUES (:event_id, :version_number, 'draft', CAST(:story AS jsonb), CAST(:metadata AS jsonb))
            RETURNING *
            """
        ),
        {
            "event_id": event_id,
            "version_number": version,
            "story": json.dumps(story),
            "metadata": json.dumps(generation_metadata),
        },
    )
    return dict(result.mappings().one())


async def update_interactions(db: AsyncSession, event_id: str, data: dict[str, Any]) -> dict[str, Any]:
    result = await db.execute(
        text(
            f"""
            UPDATE public.events
            SET interactive_data = CAST(:interactive_data AS jsonb), updated_at = now()
            WHERE (id = :event_id OR slug = :event_id) AND status IN ('draft', 'review')
            RETURNING {EVENT_COLUMNS}
            """
        ),
        {"event_id": event_id, "interactive_data": json.dumps(data)},
    )
    row = result.mappings().first()
    if row is None:
        raise ValueError("Event not found or not editable")
    return dict(row)

async def create_revision_draft(db: AsyncSession, event_id: str) -> dict[str, Any]:
    event = await get_event(db, event_id)
    if event is None:
        raise ValueError("Event not found")
    if event["status"] != "published":
        raise ValueError("Only published events can create revision drafts")

    base_slug = f"{event['slug']}-revision"
    slug = await _unique_slug(db, base_slug)
    draft = await create_event(
        db,
        {
            "id": f"event-{slug}",
            "slug": slug,
            "title": f"{event['title']} (ban nhap)",
            "era_id": event["era_id"],
            "era_slug": event["era_slug"],
            "year": event["year"],
            "type": event["type"],
            "template_type": event["template_type"],
            "summary": event["summary"],
        },
    )
    story = await get_latest_story(db, event["id"])
    if story:
        await upsert_story(
            db,
            draft["id"],
            story["story_json"],
            {**(story.get("generation_metadata") or {}), "revisionOf": event["id"]},
        )
    await update_interactions(db, draft["id"], event.get("interactive_data") or _empty_interactions())
    return draft


async def _next_story_version(db: AsyncSession, event_id: str) -> int:
    result = await db.execute(
        text("SELECT COALESCE(MAX(version_number), 0) + 1 FROM public.event_story_versions WHERE event_id = :event_id"),
        {"event_id": event_id},
    )
    return int(result.scalar_one())


def _empty_interactions() -> dict[str, Any]:
    return {"characters": [], "timeline": [], "quiz": []}

async def _require_era(db: AsyncSession, era_id: str | None, era_slug: str | None) -> dict[str, Any]:
    if not era_id and not era_slug:
        raise ValueError("A valid era is required")
    result = await db.execute(
        text(
            """
            SELECT id, slug
            FROM public.eras
            WHERE id = :era_id OR slug = :era_slug
            LIMIT 1
            """
        ),
        {"era_id": era_id, "era_slug": era_slug},
    )
    row = result.mappings().first()
    if row is None:
        raise ValueError("Era not found")
    return dict(row)

async def _require_editable_event(db: AsyncSession, event_id: str) -> dict[str, Any]:
    event = await get_event(db, event_id)
    if event is None:
        raise ValueError("Event not found")
    if event["status"] not in {"draft", "review"}:
        raise ValueError("Event is not editable")
    return event

async def _unique_slug(db: AsyncSession, base_slug: str) -> str:
    slug = base_slug
    index = 2
    while await get_event(db, slug):
        slug = f"{base_slug}-{index}"
        index += 1
    return slug
