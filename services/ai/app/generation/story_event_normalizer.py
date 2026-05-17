from copy import deepcopy
from typing import Any

from app.workspace.story_event_payload import story_event_shell

BEAT_TYPES = {"hook", "setup", "rising", "climax", "falling", "takeaway"}


def normalize_story_event_payload(
    payload: dict[str, Any] | None,
    title: str,
    template_key: str,
    flow_type: str,
    source_mode: str,
) -> dict[str, Any]:
    base = story_event_shell(title, template_key, flow_type, source_mode)
    if not payload:
        return base

    merged = deepcopy(base)
    merged.update({k: v for k, v in payload.items() if k != "eventData"})
    event_data = merged["eventData"]
    event_data.update(payload.get("eventData") or {})

    story = event_data.get("story") or {}
    beats = [_normalize_beat(beat) for beat in story.get("beats", []) if _normalize_beat(beat)]
    event_data["story"] = {
        "templateType": story.get("templateType") or template_key or "universal",
        "beats": beats,
    }

    for key in ["characters", "timeline", "quiz", "actors", "gradeTags", "topics", "relatedEventSlugs"]:
        if not isinstance(event_data.get(key), list):
            event_data[key] = []

    event_data["featured"] = False
    event_data["fallbackImage"] = event_data.get("fallbackImage") or base["eventData"]["fallbackImage"]
    event_data["theme"] = event_data.get("theme") or base["eventData"]["theme"]
    merged["pageType"] = "story-event"
    merged["flowType"] = flow_type
    merged["sourceMode"] = source_mode
    merged["title"] = event_data.get("title") or title
    return merged


def _normalize_beat(beat: Any) -> dict[str, Any] | None:
    if not isinstance(beat, dict) or beat.get("type") not in BEAT_TYPES:
        return None
    blocks = beat.get("blocks") if isinstance(beat.get("blocks"), list) else []
    return {
        "type": beat["type"],
        "title": str(beat.get("title") or beat["type"]).strip(),
        "blocks": [block for block in blocks if isinstance(block, dict)],
    }
