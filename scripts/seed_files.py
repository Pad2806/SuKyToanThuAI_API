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
    return load_json("events.json")


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


def database_url() -> str:
    value = os.environ["DATABASE_URL"]
    return value.replace("postgresql+asyncpg://", "postgresql://", 1)


def jsonb(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)

