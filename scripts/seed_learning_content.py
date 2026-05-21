from typing import Any

import asyncpg

from seed_files import GRADE_IDS


async def seed_textbook(conn: asyncpg.Connection, events: list[dict[str, Any]]) -> None:
    # Skip if migration 009 already seeded detailed textbook data
    count = await conn.fetchval(
        "SELECT COUNT(*) FROM public.textbook_parts WHERE id LIKE 'p-%'"
    )
    if count and count > 0:
        print(f"  ⏭  Textbook parts already seeded by migration ({count} parts), skipping legacy seed.")
        return

    for tag, grade_id in GRADE_IDS.items():
        part_id = f"part-{tag.lower()}"
        await conn.execute(
            """
            INSERT INTO public.textbook_parts (id, grade_id, part_number, title, order_index)
            VALUES ($1,$2,1,$3,1)
            ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, updated_at=now()
            """,
            part_id,
            grade_id,
            f"Lịch sử Việt Nam - {tag}",
        )
        await _seed_lessons(conn, tag, part_id, events)


async def seed_official_text_units(
    conn: asyncpg.Connection,
    events: list[dict[str, Any]],
    details: dict[str, dict[str, Any]],
) -> None:
    await conn.execute(
        """
        INSERT INTO public.seed_sources (id, title, publisher, curriculum, grade_tags)
        VALUES ('source-sukyai-mock', 'Sử Ký AI curated seed data', 'Sử Ký AI', 'Demo', $1)
        ON CONFLICT (id) DO UPDATE SET title=EXCLUDED.title, updated_at=now()
        """,
        ["TH", "THCS", "THPT"],
    )
    for event in events:
        merged = {**event, **details.get(event["slug"], {})}
        await conn.execute(
            """
            INSERT INTO public.official_text_units
              (id, source_id, title, body, summary, ref_type, ref_id, grade_tags,
               lesson_slug, event_slugs, keywords)
            VALUES ($1,'source-sukyai-mock',$2,$3,$4,'event',$5,$6,$7,$8,$9)
            ON CONFLICT (id) DO UPDATE SET
              title=EXCLUDED.title, body=EXCLUDED.body, summary=EXCLUDED.summary,
              grade_tags=EXCLUDED.grade_tags, event_slugs=EXCLUDED.event_slugs,
              keywords=EXCLUDED.keywords, updated_at=now()
            """,
            f"otu-{event['slug']}",
            event["title"],
            _event_body(merged),
            event.get("summary", ""),
            event["id"],
            event.get("gradeTags", []),
            event["slug"],
            [event["slug"]],
            [event["title"], event.get("location") or "", *(event.get("actors") or [])],
        )


async def _seed_lessons(
    conn: asyncpg.Connection,
    tag: str,
    part_id: str,
    events: list[dict[str, Any]],
) -> None:
    lesson_events = [event for event in events if tag in event.get("gradeTags", [])]
    for index, event in enumerate(lesson_events, start=1):
        await conn.execute(
            """
            INSERT INTO public.textbook_lessons
              (id, part_id, event_id, lesson_number, title, order_index)
            VALUES ($1,$2,$3,$4,$5,$4)
            ON CONFLICT (part_id, lesson_number) DO UPDATE SET
              event_id=EXCLUDED.event_id, title=EXCLUDED.title, updated_at=now()
            """,
            f"lesson-{tag.lower()}-{event['slug']}",
            part_id,
            event["id"],
            index,
            event["title"],
        )


def _event_body(event: dict[str, Any]) -> str:
    parts = [event.get("summary", ""), event.get("excerpt", "")]
    for beat in event.get("story", {}).get("beats", []):
        parts.append(beat.get("title", ""))
        for block in beat.get("blocks", []):
            parts.append(block.get("body") or block.get("quote") or "")
    return "\n".join(part for part in parts if part)

