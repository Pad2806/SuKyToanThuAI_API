import json

from alembic import op

revision = "007_admin_event_template_configs"
down_revision = "006_canonical_era_taxonomy"
branch_labels = None
depends_on = None

TEMPLATES = {
    "universal": ("Phổ quát", "Mẫu kể chuyện lịch sử chung.", "other", 10, 1, 3, [
        ("hero", "Ảnh bìa", "required"), ("key-figure", "Nhân vật chính", "optional"),
        ("key-place", "Địa điểm", "optional"), ("timeline-scene-1", "Cảnh mốc 1", "optional"),
        ("timeline-scene-2", "Cảnh mốc 2", "optional"), ("aftermath", "Hệ quả", "required"),
    ]),
    "battle": ("Trận đánh", "Trận đánh có bản đồ, diễn biến, cao trào và hệ quả.", "battle", 20, 3, 4, [
        ("hero", "Ảnh bìa", "required"), ("battle-map", "Bản đồ trận địa", "one-of:battle-space"),
        ("battlefield", "Chiến trường", "one-of:battle-space"), ("climax", "Cao trào", "required"),
        ("character-1", "Nhân vật 1", "optional"), ("character-2", "Nhân vật 2", "optional"),
        ("timeline-scene-1", "Cảnh mốc 1", "optional"), ("timeline-scene-2", "Cảnh mốc 2", "optional"),
        ("timeline-scene-3", "Cảnh mốc 3", "optional"), ("aftermath", "Hệ quả", "required"),
    ]),
    "battle_air_defense": ("Trận phòng không", "Chiến dịch phòng không như Điện Biên Phủ trên không.", "battle", 30, 2, 5, [
        ("hero", "Ảnh bìa", "required"), ("radar-command", "Sở chỉ huy radar", "required"),
        ("missile-site", "Trận địa tên lửa", "required"), ("air-raid-map", "Bản đồ đường bay", "required"),
        ("timeline-scene-1", "Cảnh mốc 1", "optional"), ("timeline-scene-2", "Cảnh mốc 2", "optional"),
        ("timeline-scene-3", "Cảnh mốc 3", "optional"), ("climax", "Cao trào", "required"),
        ("aftermath", "Hệ quả", "required"), ("character-1", "Nhân vật 1", "optional"),
    ]),
    "dynasty": ("Triều đại", "Nhân vật sáng lập, kinh đô, cải cách và di sản.", "dynasty", 40, 1, 3, [
        ("hero", "Ảnh bìa", "required"), ("founder", "Người sáng lập", "optional"),
        ("capital", "Kinh đô", "required"), ("reform", "Cải cách", "optional"),
        ("timeline-scene-1", "Cảnh mốc 1", "optional"), ("legacy", "Di sản", "required"),
    ]),
    "movement": ("Phong trào", "Lãnh đạo, lực lượng tham gia, bước ngoặt và hệ quả.", "movement", 50, 2, 4, [
        ("hero", "Ảnh bìa", "required"), ("leader", "Lãnh đạo", "optional"),
        ("gathering", "Tập hợp", "optional"), ("turning-point", "Bước ngoặt", "required"),
        ("timeline-scene-1", "Cảnh mốc 1", "optional"), ("aftermath", "Hệ quả", "required"),
    ]),
    "culture": ("Văn hóa", "Hiện vật, không gian, tập tục và di sản.", "culture", 60, 1, 2, [
        ("hero", "Ảnh bìa", "required"), ("artifact", "Hiện vật", "required"),
        ("setting", "Không gian", "required"), ("practice", "Tập tục", "optional"),
        ("timeline-scene-1", "Cảnh mốc 1", "optional"), ("legacy", "Di sản", "required"),
    ]),
    "diplomacy": ("Ngoại giao", "Bối cảnh, nhân vật, văn kiện và kết quả ngoại giao.", "diplomacy", 70, 2, 3, [
        ("hero", "Ảnh bìa", "required"), ("key-figure", "Nhân vật chính", "optional"),
        ("setting", "Không gian", "required"), ("turning-point", "Bước ngoặt", "required"),
        ("timeline-scene-1", "Cảnh mốc 1", "optional"), ("legacy", "Di sản", "required"),
    ]),
}

BASE_FIELDS = [
    ("title", "Tiêu đề", True),
    ("summary", "Tóm tắt", True),
    ("location", "Địa điểm", False),
    ("actors", "Nhân vật", False),
]

TEMPLATE_FIELDS = {
    "battle": [("opponent", "Đối phương", True), ("result", "Kết quả", True)],
    "battle_air_defense": [
        ("location", "Khu vực phòng không", True),
        ("opponent", "Đối phương / mục tiêu tập kích", True),
        ("result", "Kết quả đánh trả", True),
        ("actors", "Lực lượng / nhân vật", True),
    ],
    "dynasty": [("location", "Kinh đô / trung tâm quyền lực", True), ("result", "Di sản chính", True)],
    "movement": [("location", "Địa bàn phong trào", True), ("result", "Kết quả / tác động", True)],
    "culture": [("location", "Không gian văn hóa", True), ("result", "Di sản để lại", True)],
    "diplomacy": [("opponent", "Đối tượng ngoại giao", True), ("result", "Kết quả ngoại giao", True)],
}

def upgrade() -> None:
    for key, (name, description, event_type, order, characters_min, timeline_min, slots) in TEMPLATES.items():
        config = {
            "admin": {
                "enabled": True,
                "order": order,
                "name": name,
                "description": description,
                "eventType": event_type,
                "fieldGroups": _field_groups(key),
                "requirements": {
                    "charactersMin": characters_min,
                    "timelineMin": timeline_min,
                    "storyBeatsMin": 6,
                    "quizMin": 3,
                    "climaxPhasesMin": 3 if key == "battle_air_defense" else 2 if key == "battle" else 1,
                },
                "assetSlots": [
                    {"slotKey": slot_key, "slotLabel": slot_label, "requirement": requirement}
                    for slot_key, slot_label, requirement in slots
                ],
            }
        }
        payload = json.dumps(config, ensure_ascii=False).replace("'", "''")
        op.execute(f"""
            INSERT INTO public.story_templates AS current_template (template_type, name, default_theme, config)
            VALUES ('{key}', '{name}', 'vietnamese-history', '{payload}'::jsonb)
            ON CONFLICT (template_type) DO UPDATE
            SET name = EXCLUDED.name,
                default_theme = EXCLUDED.default_theme,
                config = jsonb_set(COALESCE(current_template.config, '{{}}'::jsonb), '{{admin}}', EXCLUDED.config->'admin', true)
        """)

def downgrade() -> None:
    for key in TEMPLATES:
        op.execute(f"UPDATE public.story_templates SET config = config - 'admin' WHERE template_type = '{key}'")

def _field_groups(key: str) -> list[dict]:
    fields = {field_key: {"key": field_key, "label": label, "required": required} for field_key, label, required in BASE_FIELDS}
    for field_key, label, required in TEMPLATE_FIELDS.get(key, []):
        fields[field_key] = {"key": field_key, "label": label, "required": required}
    return [{"key": "facts", "label": "Thông tin cần nhập", "fields": list(fields.values())}]
