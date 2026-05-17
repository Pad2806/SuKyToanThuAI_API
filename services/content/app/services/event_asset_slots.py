from typing import Any

SLOT_TEMPLATES = {
    "battle": [
        ("hero", "Anh bia"),
        ("battle-map", "Ban do tran dia"),
        ("battlefield", "Chien truong"),
        ("climax", "Cao trao"),
        ("character-1", "Nhan vat 1"),
        ("character-2", "Nhan vat 2"),
        ("timeline-scene-1", "Canh moc 1"),
        ("timeline-scene-2", "Canh moc 2"),
        ("timeline-scene-3", "Canh moc 3"),
        ("aftermath", "He qua"),
    ],
    "movement": [("hero", "Anh bia"), ("leader", "Lanh dao"), ("gathering", "Tap hop"), ("turning-point", "Buoc ngoat"), ("timeline-scene-1", "Canh moc 1"), ("timeline-scene-2", "Canh moc 2"), ("aftermath", "He qua")],
    "dynasty": [("hero", "Anh bia"), ("founder", "Nguoi sang lap"), ("capital", "Kinh do"), ("reform", "Cai cach"), ("timeline-scene-1", "Canh moc 1"), ("timeline-scene-2", "Canh moc 2"), ("legacy", "Di san")],
    "culture": [("hero", "Anh bia"), ("artifact", "Hien vat"), ("setting", "Khong gian"), ("practice", "Tap tuc"), ("timeline-scene-1", "Canh moc 1"), ("timeline-scene-2", "Canh moc 2"), ("legacy", "Di san")],
    "universal": [("hero", "Anh bia"), ("key-figure", "Nhan vat chinh"), ("key-place", "Dia diem"), ("timeline-scene-1", "Canh moc 1"), ("timeline-scene-2", "Canh moc 2"), ("aftermath", "He qua")],
}


def required_slots(template_type: str | None) -> list[dict[str, Any]]:
    template = template_type if template_type in SLOT_TEMPLATES else "universal"
    return [
        {"slot_key": key, "slot_label": label, "status": "missing", "metadata": {"template": template}}
        for key, label in SLOT_TEMPLATES[template]
    ]

def slot_templates() -> dict[str, list[dict[str, str]]]:
    return {
        template: [{"slotKey": key, "slotLabel": label} for key, label in slots]
        for template, slots in SLOT_TEMPLATES.items()
    }
