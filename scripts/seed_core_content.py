from typing import Any

import asyncpg

from seed_files import GRADE_IDS, jsonb
from seed_quality import seed_event_status


async def seed_eras(conn: asyncpg.Connection, eras: list[dict[str, Any]]) -> None:
    for era in eras:
        await conn.execute(
            """
            INSERT INTO public.eras
              (id, slug, name, year_range, start_year, end_year, summary,
               cover_image, fallback_image, featured_event_ids, order_index)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
            ON CONFLICT (id) DO UPDATE SET
              slug=EXCLUDED.slug, name=EXCLUDED.name, year_range=EXCLUDED.year_range,
              start_year=EXCLUDED.start_year, end_year=EXCLUDED.end_year,
              summary=EXCLUDED.summary, cover_image=EXCLUDED.cover_image,
              fallback_image=EXCLUDED.fallback_image,
              featured_event_ids=EXCLUDED.featured_event_ids,
              order_index=EXCLUDED.order_index, updated_at=now()
            """,
            era["id"],
            era["slug"],
            era["name"],
            era["yearRange"],
            era.get("startYear"),
            era.get("endYear"),
            era.get("summary", ""),
            era.get("coverImage"),
            era.get("fallbackImage"),
            era.get("featuredEventIds", []),
            era.get("order", 0),
        )


async def seed_events(
    conn: asyncpg.Connection,
    events: list[dict[str, Any]],
    details: dict[str, dict[str, Any]],
) -> None:
    for event in events:
        merged = {**event, **details.get(event["slug"], {})}
        merged["status"] = seed_event_status(merged)
        await _upsert_event(conn, merged)
        await seed_story_version(conn, merged)


async def seed_story_version(conn: asyncpg.Connection, event: dict[str, Any]) -> None:
    story = event.get("story") or {
        "templateType": event.get("templateType", "universal"),
        "beats": [{"type": "hook", "title": event["title"], "blocks": [{"type": "text", "body": event.get("summary", "")}]}],
    }
    await conn.execute(
        """
        INSERT INTO public.event_story_versions
          (event_id, version_number, status, story_json, published_at)
        VALUES ($1, 1, $2, $3::jsonb, CASE WHEN $2 = 'published' THEN now() ELSE NULL END)
        ON CONFLICT (event_id, version_number) DO UPDATE SET
          status=EXCLUDED.status, story_json=EXCLUDED.story_json,
          published_at=EXCLUDED.published_at, updated_at=now()
        """,
        event["id"],
        event["status"],
        jsonb(story),
    )


async def seed_event_grades(conn: asyncpg.Connection, events: list[dict[str, Any]]) -> None:
    for event in events:
        for tag in event.get("gradeTags", []):
            grade_id = GRADE_IDS.get(str(tag).upper())
            if grade_id:
                await conn.execute(
                    "INSERT INTO public.event_grades (event_id, grade_id) VALUES ($1,$2) ON CONFLICT DO NOTHING",
                    event["id"],
                    grade_id,
                )


async def _upsert_event(conn: asyncpg.Connection, event: dict[str, Any]) -> None:
    interactive = {
        "characters": event.get("characters", []),
        "timeline": event.get("timeline", []),
        "climaxScene": event.get("climaxScene"),
        "aftermath": event.get("aftermath"),
        "takeaway": event.get("takeaway"),
        "quiz": event.get("quiz", []),
    }
    await conn.execute(
        """
        INSERT INTO public.events
          (id, slug, title, era_id, era_slug, year, start_year, end_year,
           grade_tags, type, featured, summary, excerpt, image, fallback_image,
           location, actors, opponent, result, theme, template_type,
           related_event_slugs, interactive_data, status)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,
                $17,$18,$19,$20,$21,$22,$23::jsonb,$24)
        ON CONFLICT (id) DO UPDATE SET
          slug=EXCLUDED.slug, title=EXCLUDED.title, era_id=EXCLUDED.era_id,
          era_slug=EXCLUDED.era_slug, year=EXCLUDED.year,
          start_year=EXCLUDED.start_year, end_year=EXCLUDED.end_year,
          grade_tags=EXCLUDED.grade_tags, type=EXCLUDED.type,
          featured=EXCLUDED.featured, summary=EXCLUDED.summary,
          excerpt=EXCLUDED.excerpt, image=EXCLUDED.image,
          fallback_image=EXCLUDED.fallback_image, location=EXCLUDED.location,
          actors=EXCLUDED.actors, opponent=EXCLUDED.opponent,
          result=EXCLUDED.result, theme=EXCLUDED.theme,
          template_type=EXCLUDED.template_type,
          related_event_slugs=EXCLUDED.related_event_slugs,
          interactive_data=EXCLUDED.interactive_data, status=EXCLUDED.status,
          updated_at=now()
        """,
        event["id"],
        event["slug"],
        event["title"],
        event["eraId"],
        event["eraSlug"],
        event["year"],
        event.get("startYear"),
        event.get("endYear"),
        event.get("gradeTags", []),
        event.get("type", "other"),
        bool(event.get("featured", False)),
        event.get("summary", ""),
        event.get("excerpt", ""),
        event.get("image", ""),
        event.get("fallbackImage"),
        event.get("location"),
        event.get("actors", []),
        event.get("opponent"),
        event.get("result"),
        event.get("theme", "vietnamese-history"),
        event.get("templateType") or event.get("story", {}).get("templateType", "universal"),
        event.get("relatedEventSlugs", []),
        jsonb(interactive),
        event["status"],
    )
