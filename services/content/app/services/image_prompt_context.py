from typing import Any

BEAT_FOCUS = {
    "hero": ("hook", "setup", "takeaway"),
    "climax": ("climax",),
    "aftermath": ("falling", "takeaway"),
}

def build_slot_context(event: dict[str, Any], slot_key: str) -> str:
    event_data = _event_data(event)
    interactive = event.get("interactive_data") or {}
    parts: list[str] = []
    if slot_key.startswith("climax-phase-"):
        parts.extend(_climax_phase_context(event_data, interactive, _slot_index(slot_key)))
    elif slot_key.startswith("timeline-scene-"):
        parts.extend(_timeline_context(event_data, interactive, _slot_index(slot_key)))
        parts.extend(_beat_context(event_data, ("rising", "setup")))
    elif slot_key.startswith("character-"):
        parts.extend(_character_context(event_data, interactive, _slot_index(slot_key)))
    elif slot_key in {"battle-map", "air-raid-map"}:
        parts.extend(_timeline_context(event_data, interactive, 1))
        parts.extend(_climax_context(event_data, interactive))
    elif slot_key == "climax":
        parts.extend(_climax_context(event_data, interactive))
        parts.extend(_beat_context(event_data, BEAT_FOCUS["climax"]))
    elif slot_key == "aftermath":
        parts.extend(_aftermath_context(event_data, interactive))
        parts.extend(_beat_context(event_data, BEAT_FOCUS["aftermath"]))
    else:
        parts.extend(_beat_context(event_data, BEAT_FOCUS.get(slot_key, ("hook", "rising", "climax"))))
        parts.extend(_takeaway_context(event_data, interactive))
    return _join(parts)

def _event_data(event: dict[str, Any]) -> dict[str, Any]:
    story_json = event.get("story_json")
    if isinstance(story_json, dict):
        event_data = story_json.get("eventData")
        return event_data if isinstance(event_data, dict) else story_json
    story = event.get("story")
    if isinstance(story, dict) and isinstance(story.get("eventData"), dict):
        return story["eventData"]
    if isinstance(story, dict):
        return {**event, "story": story}
    return event

def _timeline_context(event_data: dict[str, Any], interactive: dict[str, Any], index: int) -> list[str]:
    item = _indexed_item(interactive.get("timeline"), index) or _indexed_item(event_data.get("timeline"), index)
    if not item:
        return []
    return [_clean(" ".join(str(item.get(key) or "") for key in ("day", "month", "year", "date", "title", "description", "mood")))]

def _character_context(event_data: dict[str, Any], interactive: dict[str, Any], index: int) -> list[str]:
    item = _indexed_item(interactive.get("characters"), index) or _indexed_item(event_data.get("characters"), index)
    if not item:
        return []
    return [_clean(" ".join(str(item.get(key) or "") for key in ("name", "role", "side", "bio", "quote")))]

def _climax_context(event_data: dict[str, Any], interactive: dict[str, Any]) -> list[str]:
    scene = interactive.get("climaxScene") or event_data.get("climaxScene")
    if not isinstance(scene, dict):
        return []
    parts = [_clean(scene.get("title"))]
    for phase in scene.get("phases") or []:
        if isinstance(phase, dict):
            parts.append(_clean(" ".join(str(phase.get(key) or "") for key in ("label", "summary", "description", "keyDetail"))))
    for hotspot in scene.get("hotspots") or []:
        if isinstance(hotspot, dict):
            parts.append(_clean(" ".join(str(hotspot.get(key) or "") for key in ("label", "description"))))
    return parts

def _climax_phase_context(event_data: dict[str, Any], interactive: dict[str, Any], index: int) -> list[str]:
    scene = interactive.get("climaxScene") or event_data.get("climaxScene")
    if not isinstance(scene, dict):
        return []
    phase = _indexed_item(scene.get("phases"), index)
    if not phase:
        return [_clean(scene.get("title"))]
    parts = [_clean(scene.get("title"))]
    parts.append(_clean(" ".join(str(phase.get(key) or "") for key in ("label", "summary", "description", "keyDetail"))))
    phase_id = str(phase.get("id") or phase.get("phaseId") or "").strip()
    if phase_id:
        for hotspot in scene.get("hotspots") or []:
            if isinstance(hotspot, dict) and str(hotspot.get("phaseId") or hotspot.get("phase_id") or "").strip() == phase_id:
                parts.append(_clean(" ".join(str(hotspot.get(key) or "") for key in ("label", "description"))))
    return parts

def _aftermath_context(event_data: dict[str, Any], interactive: dict[str, Any]) -> list[str]:
    aftermath = interactive.get("aftermath") or event_data.get("aftermath")
    if not isinstance(aftermath, dict):
        return []
    parts = [_clean(aftermath.get("title"))]
    for stat in aftermath.get("stats") or []:
        if isinstance(stat, dict):
            parts.append(_clean(" ".join(str(stat.get(key) or "") for key in ("label", "value", "sublabel"))))
    for key in ("before", "after"):
        section = aftermath.get(key)
        if isinstance(section, dict):
            parts.append(_clean(section.get("title")))
            parts.extend(_clean(item) for item in section.get("items") or [])
    return parts

def _takeaway_context(event_data: dict[str, Any], interactive: dict[str, Any]) -> list[str]:
    takeaway = interactive.get("takeaway") or event_data.get("takeaway")
    if not isinstance(takeaway, dict):
        return []
    return [_clean(" ".join(str(takeaway.get(key) or "") for key in ("happened", "whyItMatters", "lesson")))]

def _beat_context(event_data: dict[str, Any], beat_types: tuple[str, ...]) -> list[str]:
    beats = ((event_data.get("story") or {}).get("beats") if isinstance(event_data.get("story"), dict) else None) or []
    parts: list[str] = []
    for beat in beats:
        if not isinstance(beat, dict) or beat.get("type") not in beat_types:
            continue
        parts.append(_clean(beat.get("title")))
        for block in beat.get("blocks") or []:
            if isinstance(block, dict):
                parts.append(_clean(block.get("body") or block.get("quote") or block.get("caption")))
    return parts

def _indexed_item(items: Any, index: int) -> dict[str, Any] | None:
    if not isinstance(items, list):
        return None
    zero_index = max(0, index - 1)
    return items[zero_index] if zero_index < len(items) and isinstance(items[zero_index], dict) else None

def _slot_index(slot_key: str) -> int:
    try:
        return max(1, int(slot_key.rsplit("-", 1)[-1]))
    except ValueError:
        return 1

def _join(parts: list[str], limit: int = 620) -> str:
    text = "; ".join(part for part in parts if part)
    return f"{text[:limit].rstrip()}..." if len(text) > limit else text

def _clean(value: Any) -> str:
    return " ".join(str(value or "").split())
