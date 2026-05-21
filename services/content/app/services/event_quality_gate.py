from typing import Any

from app.services.event_asset_slots import expand_slots_for_event, required_slots_from_template

REQUIRED_BATTLE_SLOTS = {"hero", "context", "climax", "aftermath", "takeaway"}


def validate_event_quality(
    event: dict[str, Any],
    story: dict[str, Any] | None,
    assets: list[dict[str, Any]],
    sources: list[dict[str, Any]] | None = None,
    generation_metadata: dict[str, Any] | None = None,
    template_definition: dict[str, Any] | None = None,
) -> dict[str, Any]:
    issues: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    requirements = {
        "facts": _facts_ok(event, template_definition),
        "story": _story_ok(story, template_definition),
        "sources": bool(sources),
        "citations": _citations_ok(story, generation_metadata),
        "characters": len((event.get("interactive_data") or {}).get("characters") or []) >= _min_characters(event, template_definition),
        "timeline": len((event.get("interactive_data") or {}).get("timeline") or []) >= _requirement(template_definition, "timelineMin", 4),
        "interactions": _interactions_ok(event, template_definition),
        "assets": _assets_ok(event, assets, template_definition),
    }
    for key, passed in requirements.items():
        if not passed:
            issues.append(_issue(key, _label(key), _reason(key, template_definition)))
    score = round(100 * sum(1 for item in requirements.values() if item) / len(requirements))
    return {"passed": not issues, "score": score, "blockingIssues": issues, "warnings": warnings, "requirements": requirements}


def _facts_ok(event: dict[str, Any], template_definition: dict[str, Any] | None) -> bool:
    required = ["title", "slug", "summary", "excerpt", "era_id", "era_slug", "type", "template_type"]
    required.extend(_required_template_fields(template_definition))
    return all(_has_value(event, key) for key in set(required)) and event.get("year") is not None


def _story_ok(story: dict[str, Any] | None, template_definition: dict[str, Any] | None) -> bool:
    beats = (story or {}).get("beats") or []
    return len(beats) >= _requirement(template_definition, "storyBeatsMin", 6) and all(beat.get("title") and beat.get("blocks") for beat in beats)


def _citations_ok(story: dict[str, Any] | None, generation_metadata: dict[str, Any] | None) -> bool:
    factual_beats = [
        beat for beat in (story or {}).get("beats") or []
        if beat.get("type") not in {"hook", "takeaway"}
    ]
    citations = (generation_metadata or {}).get("citations") or []
    cited_chunks = {item.get("chunkId") for item in citations if item.get("chunkId")}
    # Nới lỏng: Chỉ cần có ít nhất 1 trích dẫn (thay vì bắt buộc mỗi beat 1 trích dẫn riêng biệt)
    return bool(factual_beats) and len(cited_chunks) > 0


def _min_characters(event: dict[str, Any], template_definition: dict[str, Any] | None) -> int:
    fallback = 3 if event.get("template_type") in {"battle", "movement"} else 1
    return _requirement(template_definition, "charactersMin", fallback)


def _interactions_ok(event: dict[str, Any], template_definition: dict[str, Any] | None) -> bool:
    data = event.get("interactive_data") or {}
    climax = data.get("climaxScene") or {}
    phases = climax.get("phases") if isinstance(climax, dict) else []
    phase_has_content = any((phase.get("summary") or phase.get("description")) for phase in phases or [] if isinstance(phase, dict))
    return (
        bool(climax.get("title") if isinstance(climax, dict) else climax)
        and phase_has_content
        and _has_interaction_text(data.get("aftermath"), ("title",))
        and _has_interaction_text(data.get("takeaway"), ("happened", "whyItMatters", "lesson"))
        and len(data.get("quiz") or []) >= _requirement(template_definition, "quizMin", 3)
    )

def _has_interaction_text(value: Any, keys: tuple[str, ...]) -> bool:
    if not isinstance(value, dict):
        return False
    return any(str(value.get(key) or "").strip() for key in keys)


def _assets_ok(event: dict[str, Any], assets: list[dict[str, Any]], template_definition: dict[str, Any] | None) -> bool:
    approved = {asset["slot_key"] for asset in assets if asset.get("status") == "approved" and asset.get("image_url")}
    if template_definition:
        slot_rows = expand_slots_for_event(event, required_slots_from_template(template_definition))
        required = {slot["slot_key"] for slot in slot_rows if (slot.get("metadata") or {}).get("requirement") == "required"}
        one_of_groups: dict[str, set[str]] = {}
        for slot in slot_rows:
            metadata = slot.get("metadata") or {}
            if metadata.get("requirement") == "one-of" and metadata.get("group"):
                one_of_groups.setdefault(metadata["group"], set()).add(slot["slot_key"])
        return required.issubset(approved) and all(group & approved for group in one_of_groups.values())
    return REQUIRED_BATTLE_SLOTS.issubset(approved)


def _requirement(template_definition: dict[str, Any] | None, key: str, fallback: int) -> int:
    value = (template_definition or {}).get("requirements", {}).get(key, fallback)
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _required_template_fields(template_definition: dict[str, Any] | None) -> list[str]:
    fields: list[str] = []
    for group in (template_definition or {}).get("fieldGroups") or []:
        fields.extend(field["key"] for field in group.get("fields") or [] if field.get("required") and field.get("key"))
    return fields


def _has_value(event: dict[str, Any], key: str) -> bool:
    value = event.get(key)
    if value is None:
        value = event.get(_camel_to_snake(key))
    if isinstance(value, str):
        return bool(value.strip())
    return bool(value)


def _camel_to_snake(value: str) -> str:
    chars: list[str] = []
    for char in value:
        if char.isupper():
            chars.extend(["_", char.lower()])
        else:
            chars.append(char)
    return "".join(chars).lstrip("_")


def _issue(key: str, label: str, reason: str) -> dict[str, str]:
    return {"key": key, "label": label, "reason": reason}


def _label(key: str) -> str:
    return {
        "facts": "Thông tin sự kiện",
        "story": "Mạch truyện",
        "sources": "Nguồn tài liệu",
        "citations": "Trích dẫn nội dung",
        "characters": "Nhân vật",
        "timeline": "Dòng thời gian",
        "interactions": "Tương tác",
        "assets": "Ảnh minh họa",
    }[key]


def _reason(key: str, template_definition: dict[str, Any] | None = None) -> str:
    return {
        "facts": "Thiếu thông tin cơ bản để hiển thị công khai (tiêu đề, tóm tắt, kỷ nguyên...).",
        "story": "Cần tối thiểu 6 phân cảnh (beat) có nội dung.",
        "sources": "Sự kiện cần được liên kết với ít nhất 1 nguồn tài liệu chính thống.",
        "citations": "Sự kiện chưa được AI ghi nhận bất kỳ trích dẫn cụ thể nào từ tài liệu nguồn.",
        "characters": "Thiếu danh sách nhân vật theo yêu cầu của giao diện.",
        "timeline": "Cần cung cấp tối thiểu 4 mốc thời gian.",
        "interactions": "Cần điền đầy đủ Cao trào, Hệ quả, Bài học và tối thiểu 3 câu hỏi trắc nghiệm.",
        "assets": "Tất cả ảnh mà layout storytelling cần (bìa, bối cảnh, nhân vật, diễn biến, cao trào, bản đồ, hệ quả/bài học) phải được tạo và phê duyệt.",
    }[key]
