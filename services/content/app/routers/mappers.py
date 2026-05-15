from collections.abc import Mapping
from typing import Any


def era_from_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "slug": row["slug"],
        "name": row["name"],
        "yearRange": row["year_range"],
        "startYear": row["start_year"],
        "endYear": row["end_year"],
        "summary": row["summary"],
        "coverImage": row["cover_image"],
        "fallbackImage": row["fallback_image"],
        "order": row["order_index"],
        "featuredEventIds": list(row["featured_event_ids"] or []),
    }


def event_from_row(row: Mapping[str, Any], include_story: bool = False) -> dict[str, Any]:
    interactive = dict(row.get("interactive_data") or {})
    event = {
        "id": row["id"],
        "slug": row["slug"],
        "title": row["title"],
        "eraId": row["era_id"],
        "eraSlug": row["era_slug"],
        "year": row["year"],
        "startYear": row["start_year"],
        "endYear": row["end_year"],
        "gradeTags": list(row["grade_tags"] or []),
        "type": row["type"],
        "topics": [row["type"]],
        "featured": row["featured"],
        "summary": row["summary"],
        "excerpt": row["excerpt"],
        "image": row["image"],
        "fallbackImage": row["fallback_image"],
        "location": row["location"],
        "actors": list(row["actors"] or []),
        "opponent": row["opponent"],
        "result": row["result"],
        "theme": row["theme"],
        "templateType": row["template_type"],
        "relatedEventSlugs": list(row["related_event_slugs"] or []),
    }
    if include_story:
        event.update(
            {
                "characters": interactive.get("characters", []),
                "timeline": interactive.get("timeline", []),
                "climaxScene": interactive.get("climaxScene"),
                "aftermath": interactive.get("aftermath"),
                "takeaway": interactive.get("takeaway"),
                "quiz": interactive.get("quiz", []),
                "story": row.get("story") or {"templateType": row["template_type"], "beats": []},
            }
        )
    return event


def grade_from_row(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "tag": row["tag"],
        "label": row["label"],
        "order": row["order_index"],
    }

