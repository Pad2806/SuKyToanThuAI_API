from copy import deepcopy
from typing import Any

DEFAULT_IMAGE = "/images/generated/parchment.png"
BEAT_TYPES = {"hook", "setup", "rising", "climax", "falling", "takeaway"}


def story_event_shell(title: str, template: str = "universal") -> dict[str, Any]:
    clean_title = (title or "Su kien moi").strip()
    return {"templateType": template or "universal", "beats": [], "title": clean_title}


def normalize_story(story: dict[str, Any] | None, title: str, template: str) -> dict[str, Any]:
    base = story_event_shell(title, template)
    if not isinstance(story, dict):
        return base
    result = deepcopy(base)
    result.update({k: v for k, v in story.items() if k != "beats"})
    result["templateType"] = result.get("templateType") or template or "universal"
    beats = story.get("beats") if isinstance(story.get("beats"), list) else []
    result["beats"] = [beat for beat in (_normalize_beat(item) for item in beats) if beat]
    return result


def event_payload_from_rows(event: dict[str, Any], story: dict[str, Any] | None) -> dict[str, Any]:
    interactive = event.get("interactive_data") or {}
    template = event.get("template_type") or "universal"
    title = event.get("title") or "Su kien moi"
    return {
        "id": event.get("id"),
        "slug": event.get("slug"),
        "title": title,
        "eraId": event.get("era_id"),
        "eraSlug": event.get("era_slug"),
        "year": event.get("year"),
        "startYear": event.get("start_year"),
        "endYear": event.get("end_year"),
        "gradeTags": list(event.get("grade_tags") or []),
        "topics": [event.get("type") or "other"],
        "type": event.get("type") or "other",
        "featured": bool(event.get("featured")),
        "summary": event.get("summary") or "",
        "excerpt": event.get("excerpt") or "",
        "image": event.get("image") or None,
        "fallbackImage": event.get("fallback_image") or DEFAULT_IMAGE,
        "location": event.get("location"),
        "actors": list(event.get("actors") or []),
        "opponent": event.get("opponent"),
        "result": event.get("result"),
        "characters": interactive.get("characters") or [],
        "timeline": interactive.get("timeline") or [],
        "climaxScene": interactive.get("climaxScene"),
        "aftermath": interactive.get("aftermath"),
        "takeaway": interactive.get("takeaway"),
        "quiz": interactive.get("quiz") or [],
        "story": normalize_story(story, title, template),
        "theme": event.get("theme") or "vietnamese-history",
        "relatedEventSlugs": list(event.get("related_event_slugs") or []),
    }


def _normalize_beat(beat: Any) -> dict[str, Any] | None:
    if not isinstance(beat, dict) or beat.get("type") not in BEAT_TYPES:
        return None
    blocks = beat.get("blocks") if isinstance(beat.get("blocks"), list) else []
    return {
        "type": beat["type"],
        "title": str(beat.get("title") or beat["type"]).strip(),
        "blocks": [block for block in blocks if isinstance(block, dict)],
    }
