import json
from typing import Any

from alembic import op
from sqlalchemy import text

revision = "008_tactical_climax_slots"
down_revision = "007_admin_event_template_configs"
branch_labels = None
depends_on = None

BATTLE_SLOTS = [
    ("hero", "Ảnh bìa", "required"),
    ("battle-map", "Bản đồ trận địa", "one-of:battle-space"),
    ("battlefield", "Chiến trường", "one-of:battle-space"),
    ("climax-phase-1", "Cao trào 1 - mở đầu", "required"),
    ("climax-phase-2", "Cao trào 2 - bước ngoặt", "required"),
    ("climax-phase-3", "Cao trào 3 - kết thúc", "required"),
    ("climax", "Nền khu vực cao trào", "optional"),
    ("character-1", "Nhân vật 1", "optional"),
    ("character-2", "Nhân vật 2", "optional"),
    ("timeline-scene-1", "Cảnh mốc 1", "optional"),
    ("timeline-scene-2", "Cảnh mốc 2", "optional"),
    ("timeline-scene-3", "Cảnh mốc 3", "optional"),
    ("aftermath", "Hệ quả", "required"),
]

AIR_DEFENSE_SLOTS = [
    ("hero", "Ảnh bìa", "required"),
    ("radar-command", "Sở chỉ huy radar", "required"),
    ("missile-site", "Trận địa tên lửa", "required"),
    ("air-raid-map", "Bản đồ đường bay", "required"),
    ("climax-phase-1", "Cao trào 1 - mở đầu", "required"),
    ("climax-phase-2", "Cao trào 2 - bước ngoặt", "required"),
    ("climax-phase-3", "Cao trào 3 - kết thúc", "required"),
    ("timeline-scene-1", "Cảnh mốc 1", "optional"),
    ("timeline-scene-2", "Cảnh mốc 2", "optional"),
    ("timeline-scene-3", "Cảnh mốc 3", "optional"),
    ("climax", "Nền khu vực cao trào", "optional"),
    ("aftermath", "Hệ quả", "required"),
    ("character-1", "Nhân vật 1", "optional"),
]

UPDATES = {"battle": BATTLE_SLOTS, "battle_air_defense": AIR_DEFENSE_SLOTS}


def upgrade() -> None:
    connection = op.get_bind()
    for template_type, slots in UPDATES.items():
        row = connection.execute(
            text("SELECT config FROM public.story_templates WHERE template_type = :template_type"),
            {"template_type": template_type},
        ).mappings().first()
        if not row:
            continue
        config = _json(row.get("config"))
        admin = config.get("admin") if isinstance(config.get("admin"), dict) else {}
        admin["requirements"] = {**(admin.get("requirements") or {}), "climaxPhasesMin": 3}
        admin["assetSlots"] = [
            {"slotKey": key, "slotLabel": label, "requirement": requirement}
            for key, label, requirement in slots
        ]
        connection.execute(
            text("""
                UPDATE public.story_templates
                SET config = jsonb_set(COALESCE(config, '{}'::jsonb), '{admin}', CAST(:admin AS jsonb), true)
                WHERE template_type = :template_type
            """),
            {"template_type": template_type, "admin": json.dumps(admin, ensure_ascii=False)},
        )


def downgrade() -> None:
    pass


def _json(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}
