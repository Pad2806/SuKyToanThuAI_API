from copy import deepcopy
from typing import Any

from app.workspace.story_event_payload import story_event_shell

BEAT_TYPES = {"hook", "setup", "rising", "climax", "falling", "takeaway", "timeline", "overview"}


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
    beats = []
    for beat in story.get("beats", []):
        normalized = _normalize_beat(beat)
        if normalized:
            beats.append(normalized)
    event_data["story"] = {
        "templateType": story.get("templateType") or template_key or "universal",
        "beats": beats,
    }

    for key in ["characters", "timeline", "quiz", "actors", "gradeTags", "topics", "relatedEventSlugs"]:
        if not isinstance(event_data.get(key), list):
            event_data[key] = []

    event_data["climaxScene"] = _normalize_climax_scene(event_data)
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
    # return {
    #     "type": beat["type"],
    #     "title": str(beat.get("title") or beat["type"]).strip(),
    #     "blocks": [block for block in blocks if isinstance(block, dict)],
    normalized_blocks = [_normalize_block(block) for block in blocks]
    return {
        "type": beat["type"],
        "title": str(beat.get("title") or beat["type"]).strip(),
        "blocks": [block for block in normalized_blocks if block],
    }


def _normalize_block(block: Any) -> dict[str, Any] | None:
    if not isinstance(block, dict):
        return None
    block_type = block.get("type")
    if block_type == "text":
        return block if str(block.get("body") or "").strip() else None
    if block_type == "quote":
        return block if str(block.get("quote") or "").strip() else None
    if block_type == "image":
        return block if block.get("image") or block.get("caption") else None
    if block_type == "quick-facts":
        return block if isinstance(block.get("items"), list) and block["items"] else None
    return block


def _normalize_climax_scene(event_data: dict[str, Any]) -> dict[str, Any] | None:
    scene = event_data.get("climaxScene")
    if isinstance(scene, dict) and isinstance(scene.get("phases"), list) and scene["phases"]:
        scene["phases"] = scene["phases"][:3]
        if not isinstance(scene.get("hotspots"), list):
            scene["hotspots"] = []
        return scene

    story = event_data.get("story") if isinstance(event_data.get("story"), dict) else {}
    template_type = story.get("templateType") or event_data.get("type")
    if template_type not in {"battle", "war", "universal"} and event_data.get("type") not in {"battle", "war"}:
        return None

    text = event_data.get("climax")
    if not text:
        for beat in event_data.get("story", {}).get("beats", []):
            if beat.get("type") != "climax":
                continue
            blocks = beat.get("blocks") if isinstance(beat.get("blocks"), list) else []
            text_blocks = [
                block.get("body") or block.get("quote")
                for block in blocks
                if block.get("type") in {"text", "quote"} and (block.get("body") or block.get("quote"))
            ]
            text = " ".join(text_blocks)
            break
    if not text:
        text = event_data.get("summary") or event_data.get("excerpt") or event_data.get("title")
    if not text:
        return None

    title = event_data.get("title") or "Cao trào"
    phase_defs = [
        ("phase-1", "Mở màn", "Bước mở đầu của cao trào"),
        ("phase-2", "Đỉnh điểm", "Hành động chính làm cục diện thay đổi"),
        ("phase-3", "Kết cục", "Kết quả trực tiếp của cao trào"),
    ]
    return {
        "title": title,
        "backgroundImage": None,
        "phases": [
            {
                "id": phase_id,
                "label": label,
                "summary": summary,
                "description": text,
                "keyDetail": None,
                "image_prompt": None,
            }
            for phase_id, label, summary in phase_defs
        ],
        "hotspots": [],
    }
