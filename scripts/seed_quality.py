from typing import Any


def seed_event_status(event: dict[str, Any]) -> str:
    if event.get("status") in {"draft", "review", "published", "archived"}:
        return event["status"]
    return "published" if seed_event_quality_passes(event) else "review"


def seed_event_quality_passes(event: dict[str, Any]) -> bool:
    story = event.get("story") or {}
    beats = story.get("beats") or []
    return all(
        [
            event.get("title"),
            event.get("slug"),
            event.get("summary"),
            event.get("excerpt"),
            event.get("image"),
            len(beats) >= 6,
            len(event.get("characters") or []) >= _min_characters(event),
            len(event.get("timeline") or []) >= 4,
            bool(event.get("climaxScene")),
            bool(event.get("aftermath")),
            bool(event.get("takeaway")),
            len(event.get("quiz") or []) >= 3,
        ]
    )


def _min_characters(event: dict[str, Any]) -> int:
    return 3 if event.get("type") in {"battle", "movement"} else 1
