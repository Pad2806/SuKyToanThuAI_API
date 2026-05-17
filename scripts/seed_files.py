import json
import os
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "seed-json"

GRADE_IDS = {
    "TH": "grade-th",
    "4": "grade-4",
    "5": "grade-5",
    "THCS": "grade-thcs",
    "6": "grade-6",
    "7": "grade-7",
    "8": "grade-8",
    "9": "grade-9",
    "THPT": "grade-thpt",
    "10": "grade-10",
    "11": "grade-11",
    "12": "grade-12",
}


def load_eras() -> list[dict[str, Any]]:
    return load_json("eras.json")


def load_events() -> list[dict[str, Any]]:
    events = load_json("events.json")
    known = {event["slug"] for event in events}
    for detail in load_details().values():
        if detail["slug"] not in known:
            events.append(_summary_from_detail(detail))
            known.add(detail["slug"])
    return events


def load_details() -> dict[str, dict[str, Any]]:
    details = {}
    for path in DATA_DIR.glob("*.json"):
        if path.name in {"eras.json", "events.json"}:
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        details[data["slug"]] = data
    return details


def load_json(name: str) -> Any:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))


def validate_seed_references(eras: list[dict[str, Any]], events: list[dict[str, Any]]) -> None:
    era_ids = {era["id"] for era in eras}
    missing = [
        f"{event['slug']} -> {event.get('eraId')}"
        for event in events
        if event.get("eraId") not in era_ids
    ]
    if missing:
        raise ValueError("Seed events reference missing eras: " + ", ".join(missing))


def database_url() -> str:
    value = os.environ["DATABASE_URL"]
    return value.replace("postgresql+asyncpg://", "postgresql://", 1)


def jsonb(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)

def _summary_from_detail(detail: dict[str, Any]) -> dict[str, Any]:
    keys = [
        "id", "slug", "title", "eraId", "eraSlug", "year", "startYear", "endYear",
        "gradeTags", "type", "featured", "summary", "excerpt", "image",
        "fallbackImage", "location", "actors", "opponent", "result",
    ]
    return {key: detail[key] for key in keys if key in detail}
