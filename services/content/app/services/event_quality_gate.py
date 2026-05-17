from typing import Any

REQUIRED_BATTLE_SLOTS = {"hero", "climax", "aftermath"}


def validate_event_quality(
    event: dict[str, Any],
    story: dict[str, Any] | None,
    assets: list[dict[str, Any]],
    sources: list[dict[str, Any]] | None = None,
    generation_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    requirements = {
        "facts": _facts_ok(event),
        "story": _story_ok(story),
        "sources": bool(sources),
        "citations": _citations_ok(story, generation_metadata),
        "characters": len((event.get("interactive_data") or {}).get("characters") or []) >= _min_characters(event),
        "timeline": len((event.get("interactive_data") or {}).get("timeline") or []) >= 4,
        "interactions": _interactions_ok(event),
        "assets": _assets_ok(event, assets),
    }
    for key, passed in requirements.items():
        if not passed:
            issues.append(_issue(key, _label(key), _reason(key)))
    score = round(100 * sum(1 for item in requirements.values() if item) / len(requirements))
    return {"passed": not issues, "score": score, "blockingIssues": issues, "warnings": warnings, "requirements": requirements}


def _facts_ok(event: dict[str, Any]) -> bool:
    required = ["title", "slug", "summary", "excerpt", "era_id", "era_slug", "type", "template_type"]
    return all(bool(event.get(key)) for key in required) and event.get("year") is not None


def _story_ok(story: dict[str, Any] | None) -> bool:
    beats = (story or {}).get("beats") or []
    return len(beats) >= 6 and all(beat.get("title") and beat.get("blocks") for beat in beats)


def _citations_ok(story: dict[str, Any] | None, generation_metadata: dict[str, Any] | None) -> bool:
    factual_beats = [
        beat for beat in (story or {}).get("beats") or []
        if beat.get("type") not in {"hook", "takeaway"}
    ]
    citations = (generation_metadata or {}).get("citations") or []
    cited_chunks = {item.get("chunkId") for item in citations if item.get("chunkId")}
    return bool(factual_beats) and len(cited_chunks) >= len(factual_beats)


def _min_characters(event: dict[str, Any]) -> int:
    return 3 if event.get("template_type") in {"battle", "movement"} else 1


def _interactions_ok(event: dict[str, Any]) -> bool:
    data = event.get("interactive_data") or {}
    return bool(data.get("climaxScene")) and bool(data.get("aftermath")) and bool(data.get("takeaway")) and len(data.get("quiz") or []) >= 3


def _assets_ok(event: dict[str, Any], assets: list[dict[str, Any]]) -> bool:
    approved = {asset["slot_key"] for asset in assets if asset.get("status") == "approved" and asset.get("image_url")}
    if event.get("template_type") == "battle":
        return REQUIRED_BATTLE_SLOTS.issubset(approved) and any(slot in approved for slot in {"battle-map", "battlefield"})
    return "hero" in approved


def _issue(key: str, label: str, reason: str) -> dict[str, str]:
    return {"key": key, "label": label, "reason": reason}


def _label(key: str) -> str:
    return {
        "facts": "Thong tin su kien",
        "story": "Mach truyen",
        "sources": "Nguon trich dan",
        "citations": "Trich dan noi dung",
        "characters": "Nhan vat",
        "timeline": "Dong thoi gian",
        "interactions": "Tuong tac",
        "assets": "Anh minh hoa",
    }[key]


def _reason(key: str) -> str:
    return {
        "facts": "Thieu thong tin co ban de hien thi cong khai.",
        "story": "Can toi thieu 6 beat co noi dung.",
        "sources": "Can co nguon chinh thong da import.",
        "citations": "Moi beat su kien can duoc neo vao chunk nguon chinh thong.",
        "characters": "Thieu danh sach nhan vat theo template.",
        "timeline": "Can toi thieu 4 moc thoi gian.",
        "interactions": "Can climax, aftermath, takeaway va quiz.",
        "assets": "Can du anh bat buoc da duoc admin duyet.",
    }[key]
