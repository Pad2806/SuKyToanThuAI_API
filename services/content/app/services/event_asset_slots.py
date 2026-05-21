import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

DEFAULT_TEMPLATES: dict[str, dict[str, Any]] = {
    "universal": {
        "name": "Phổ quát",
        "description": "Mẫu kể chuyện lịch sử chung.",
        "eventType": "other",
        "requirements": {"charactersMin": 1, "timelineMin": 3, "storyBeatsMin": 6, "quizMin": 3},
        "assetSlots": [
            ("hero", "Ảnh bìa", "required"),
            ("context", "Bối cảnh", "required"),
            ("climax", "Cao trào", "required"),
            ("aftermath", "Hệ quả", "required"),
            ("takeaway", "Bài học", "required"),
        ],
    },
    "battle": {
        "name": "Trận đánh",
        "description": "Mẫu chiến trận với diễn biến và cao trào.",
        "eventType": "battle",
        "requirements": {"charactersMin": 1, "timelineMin": 3, "storyBeatsMin": 6, "quizMin": 3},
        "assetSlots": [
            ("hero", "Ảnh bìa", "required"),
            ("context", "Bối cảnh", "required"),
            ("climax", "Cao trào", "required"),
            ("battle-map", "Bản đồ chiến thuật", "required"),
            ("aftermath", "Hệ quả", "required"),
            ("takeaway", "Bài học", "required"),
        ],
    },
    "battle_air_defense": {
        "name": "Trận phòng không",
        "description": "Mẫu phòng không chiến thuật.",
        "eventType": "battle",
        "requirements": {"charactersMin": 1, "timelineMin": 3, "storyBeatsMin": 6, "quizMin": 3},
        "assetSlots": [
            ("hero", "Ảnh bìa", "required"),
            ("context", "Bối cảnh", "required"),
            ("climax", "Cao trào", "required"),
            ("air-raid-map", "Bản đồ chiến thuật", "required"),
            ("aftermath", "Hệ quả", "required"),
            ("takeaway", "Bài học", "required"),
        ],
    },
    "dynasty": {
        "name": "Triều đại",
        "description": "Kể chuyện triều đại lịch sử.",
        "eventType": "dynasty",
        "requirements": {"charactersMin": 1, "timelineMin": 3, "storyBeatsMin": 6, "quizMin": 3},
        "assetSlots": [
            ("hero", "Ảnh bìa", "required"),
            ("context", "Bối cảnh", "required"),
            ("climax", "Cao trào", "required"),
            ("aftermath", "Hệ quả", "required"),
            ("takeaway", "Bài học", "required"),
        ],
    },
    "movement": {
        "name": "Phong trào",
        "description": "Phong trào đấu tranh và đấu tranh cách mạng.",
        "eventType": "movement",
        "requirements": {"charactersMin": 1, "timelineMin": 3, "storyBeatsMin": 6, "quizMin": 3},
        "assetSlots": [
            ("hero", "Ảnh bìa", "required"),
            ("context", "Bối cảnh", "required"),
            ("climax", "Cao trào", "required"),
            ("aftermath", "Hệ quả", "required"),
            ("takeaway", "Bài học", "required"),
        ],
    },
    "culture": {
        "name": "Văn hóa",
        "description": "Văn hóa nghệ thuật lịch sử.",
        "eventType": "culture",
        "requirements": {"charactersMin": 1, "timelineMin": 3, "storyBeatsMin": 6, "quizMin": 3},
        "assetSlots": [
            ("hero", "Ảnh bìa", "required"),
            ("context", "Bối cảnh", "required"),
            ("climax", "Cao trào", "required"),
            ("aftermath", "Hệ quả", "required"),
            ("takeaway", "Bài học", "required"),
        ],
    },
    "diplomacy": {
        "name": "Ngoại giao",
        "description": "Lịch sử ngoại giao bang giao.",
        "eventType": "diplomacy",
        "requirements": {"charactersMin": 1, "timelineMin": 3, "storyBeatsMin": 6, "quizMin": 3},
        "assetSlots": [
            ("hero", "Ảnh bìa", "required"),
            ("context", "Bối cảnh", "required"),
            ("climax", "Cao trào", "required"),
            ("aftermath", "Hệ quả", "required"),
            ("takeaway", "Bài học", "required"),
        ],
    },
}

async def list_admin_templates(db: AsyncSession) -> list[dict[str, Any]]:
    result = await db.execute(text("""
        SELECT template_type, name, default_theme, config
        FROM public.story_templates
        WHERE COALESCE(config->'admin'->>'enabled', 'true') = 'true'
        ORDER BY COALESCE((config->'admin'->>'order')::int, 999), template_type
    """))
    rows = [dict(row) for row in result.mappings().all()]
    return [_normalize_template(row) for row in rows] or _default_definitions()

async def get_admin_template(db: AsyncSession, template_type: str | None) -> dict[str, Any]:
    key = template_type or "universal"
    result = await db.execute(
        text("SELECT template_type, name, default_theme, config FROM public.story_templates WHERE template_type = :key LIMIT 1"),
        {"key": key},
    )
    row = result.mappings().first()
    return _normalize_template(dict(row)) if row else _default_definition(key)

async def required_slots(db: AsyncSession, template_type: str | None) -> list[dict[str, Any]]:
    return required_slots_from_template(await get_admin_template(db, template_type))

def required_slots_from_template(template: dict[str, Any]) -> list[dict[str, Any]]:
    key = template.get("templateType") or "universal"
    rows = []
    for slot in template.get("assetSlots") or []:
        rows.append({
            "slot_key": slot["slotKey"],
            "slot_label": slot.get("slotLabel") or slot["slotKey"],
            "status": "missing",
            "metadata": {"template": key, "requirement": slot.get("requirement", "optional"), "group": slot.get("group")},
        })
    return rows

def expand_slots_for_event(event: dict[str, Any], slots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = list(slots)
    existing = {slot.get("slot_key") for slot in rows}
    template = event.get("template_type") or "universal"
    data = event.get("interactive_data") or {}

    def add(slot_key: str, slot_label: str, requirement: str = "required") -> None:
        if slot_key in existing:
            return
        existing.add(slot_key)
        rows.append({
            "slot_key": slot_key,
            "slot_label": slot_label,
            "status": "missing",
            "metadata": {"template": template, "requirement": requirement},
        })

    for index, character in enumerate(data.get("characters") or [], start=1):
        add(f"character-{index}", f"Nhân vật {index}: {_item_title(character, 'Chân dung')}")

    for index, milestone in enumerate(data.get("timeline") or [], start=1):
        add(f"timeline-scene-{index}", f"Diễn biến {index}: {_item_title(milestone, 'Mốc sự kiện')}")

    climax = data.get("climaxScene") or {}
    for index, phase in enumerate(climax.get("phases") or [], start=1):
        add(f"climax-phase-{index}", f"Giai đoạn then chốt {index}: {_item_title(phase, 'Cao trào')}")

    if climax.get("hotspots") and "battle-map" not in existing and "air-raid-map" not in existing:
        map_key = "air-raid-map" if template == "battle_air_defense" else "battle-map"
        add(map_key, "Bản đồ chiến thuật")

    return rows

def slot_templates(templates: list[dict[str, Any]] | None = None) -> dict[str, list[dict[str, str]]]:
    definitions = templates or _default_definitions()
    return {
        item["templateType"]: [
            {"slotKey": slot["slotKey"], "slotLabel": slot["slotLabel"], "requirement": slot.get("requirement", "optional")}
            for slot in item.get("assetSlots", [])
        ]
        for item in definitions
    }

def _normalize_template(row: dict[str, Any]) -> dict[str, Any]:
    config = _json(row.get("config"))
    admin = config.get("admin") if isinstance(config.get("admin"), dict) else config
    fallback = DEFAULT_TEMPLATES.get(row.get("template_type"), DEFAULT_TEMPLATES["universal"])
    return {
        "templateType": row.get("template_type") or "universal",
        "name": admin.get("name") or row.get("name") or fallback["name"],
        "description": admin.get("description") or fallback["description"],
        "eventType": admin.get("eventType") or fallback["eventType"],
        "defaultTheme": row.get("default_theme") or "vietnamese-history",
        "fieldGroups": admin.get("fieldGroups") or _field_groups(),
        "requirements": {**fallback.get("requirements", {}), **(admin.get("requirements") or {})},
        "assetSlots": _normalize_slots(fallback["assetSlots"]),
    }

def _normalize_slots(slots: list[Any]) -> list[dict[str, Any]]:
    rows = []
    for slot in slots:
        if isinstance(slot, (list, tuple)):
            key, label, requirement = slot
            slot = {"slotKey": key, "slotLabel": label, "requirement": requirement}
        requirement = slot.get("requirement") or "optional"
        group = slot.get("group")
        if isinstance(requirement, str) and requirement.startswith("one-of:"):
            group = requirement.split(":", 1)[1]
            requirement = "one-of"
        rows.append({**slot, "requirement": requirement, "group": group})
    return rows

def _default_definitions() -> list[dict[str, Any]]:
    return [_default_definition(key) for key in DEFAULT_TEMPLATES]

def _default_definition(key: str) -> dict[str, Any]:
    template_key = key if key in DEFAULT_TEMPLATES else "universal"
    data = DEFAULT_TEMPLATES[template_key]
    return _normalize_template({"template_type": template_key, "name": data["name"], "config": {"admin": data}})

def _field_groups() -> list[dict[str, Any]]:
    return [{"key": "facts", "label": "Thông tin sự kiện", "fields": [{"key": "title", "required": True}, {"key": "summary", "required": True}, {"key": "location", "required": False}, {"key": "actors", "required": False}]}]

def _json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}

def _item_title(value: Any, fallback: str) -> str:
    if isinstance(value, dict):
        return str(value.get("name") or value.get("title") or value.get("label") or fallback).strip()
    return fallback
