import hashlib
import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.admin_rag_retriever import AdminChunk, retrieve_admin_chunks
from pydantic import ValidationError

from app.services.story_event_contract import (
    normalize_story_event_envelope,
    story_event_json_schema,
    validate_story_event,
)
from app.services.vertex_text_client import VertexTextClient


class AdminDraftGenerator:
    def __init__(self, client: VertexTextClient | None = None) -> None:
        self.client = client or VertexTextClient()

    async def draft_event(
        self,
        db: AsyncSession,
        *,
        event: dict[str, Any],
        source_ids: list[str],
        query: str | None,
    ) -> dict[str, Any]:
        chunks = await retrieve_admin_chunks(db, event["id"], source_ids)
        await _release_db_connection(db)
        if not chunks:
            return {"status": "no_data", "detail": "Chua co nguon chinh thong san sang cho su kien nay."}
        prompt = _build_prompt(event, chunks, query)
        raw = await self.client.generate_json(prompt, story_event_json_schema())
        draft = _validate_or_repair_envelope(raw)
        allowed_chunks = {chunk.id for chunk in chunks}
        invalid = [item.chunkId for item in draft.citations if item.chunkId and item.chunkId not in allowed_chunks]
        if invalid:
            raise ValueError("Gemini returned citations outside selected source chunks")
        payload = draft.model_dump(by_alias=True)
        _complete_admin_event_data(payload.get("eventData") or {})
        payload["coverageReport"] = _coverage_report(payload.get("eventData") or {})
        payload["generationMetadata"] = {
            "provider": "vertex",
            "model": self.client.settings.ai_draft_model,
            "sourceIds": source_ids,
            "promptHash": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        }
        return {"status": "drafted", "payload": payload}


async def _release_db_connection(db: AsyncSession | None) -> None:
    if db is not None:
        await db.rollback()


def _build_prompt(event: dict[str, Any], chunks: list[AdminChunk], query: str | None) -> str:
    context = "\n\n".join(
        f"[chunk:{chunk.id}] {chunk.title}\n{chunk.content[:1800]}" for chunk in chunks
    )
    facts = json.dumps(
        {
            "id": event["id"],
            "slug": event["slug"],
            "title": event["title"],
            "summary": event["summary"],
            "year": event["year"],
            "type": event["type"],
            "templateType": event["template_type"],
        },
        ensure_ascii=False,
    )
    return f"""
You are drafting an official Vietnamese history story-event page.
Return one JSON object that validates exactly as the provided schema.
Required envelope values:
- pageType: "story-event"
- flowType: "system_data"
- sourceMode: "research"
Use only the provided source chunks. If data is missing, return null or empty arrays.
Do not invent dates, people, places, outcomes, citations, or image details.
Every factual section should cite source chunk ids when possible.
For citation chunkId fields, use only ids shown in [chunk:<id>] markers.
Characters must include side: "ally" for Vietnamese/admin-side forces, "enemy" for opposing forces, "other" for neutral.
Timeline items must include day/month/year when known. If only month/year is known, leave day empty. If only year is known, leave day and month empty.
climaxScene must include a title and concrete phases with summary/description derived from source chunks.
Draft enough content for the published storytelling page, not only short card summaries:
- story.beats must include hook, setup, rising, climax, falling, takeaway. Each beat should include 2-4 text/quote/quick-facts blocks when the source chunks support it.
- setup/Bối cảnh needs a detailed historical context and quick facts.
- characters need name, side, role, traits, contribution, description, and imagePrompt.
- timeline needs order, date/time, title, summary, description, keyPoints, and imagePrompt for each milestone.
- climaxScene needs title, summary, description, quote if supported, phases with label/summary/description/keyDetail, and hotspots with label/description/tacticalRole when a tactical map is supported.
- aftermath needs title, description, consequences, lessons, historicalMeaning, and stats when supported.
- takeaway needs happened, whyItMatters, and lesson with substantive text.
- quiz should include at least 3 questions with options, correct index, and explanation.
- imagePrompt fields should describe what to generate, but factual visual details must come from source chunks.

Event facts:
{facts}

Admin request:
{query or "Create a complete review draft for the event."}

Source chunks:
{context}
"""

def _validate_or_repair_envelope(raw: dict[str, Any]):
    try:
        return validate_story_event(raw)
    except ValidationError as first_error:
        repaired = normalize_story_event_envelope(raw)
        try:
            return validate_story_event(repaired)
        except ValidationError as second_error:
            raise ValueError(str(second_error)) from first_error

def _complete_admin_event_data(event_data: dict[str, Any]) -> None:
    _normalize_story_section_objects(event_data)
    _complete_character_sides(event_data)
    _complete_interaction_details(event_data)
    _complete_climax_scene(event_data)
    for item in event_data.get("timeline") or []:
        if isinstance(item, dict):
            item.setdefault("day", "")
            item.setdefault("month", "")
            item.setdefault("date", _timeline_date_label(item))

def _normalize_story_section_objects(event_data: dict[str, Any]) -> None:
    story = event_data.setdefault(
        "story",
        {"templateType": event_data.get("templateType") or event_data.get("type") or "universal", "beats": []},
    )
    story.setdefault("beats", [])
    context = event_data.get("context")
    if isinstance(context, dict):
        setup = _ensure_beat(story, "setup", context.get("title") or "Bối cảnh")
        _append_text_block(setup, _join_values(context.get("description"), context.get("paragraphs")))
        facts = context.get("quickFacts") or context.get("facts")
        if isinstance(facts, list) and facts and not any(block.get("type") == "quick-facts" for block in setup.get("blocks", [])):
            setup.setdefault("blocks", []).append({"type": "quick-facts", "title": "Dữ kiện nhanh", "items": facts})
    hero = event_data.get("hero")
    if isinstance(hero, dict):
        event_data["summary"] = event_data.get("summary") or hero.get("summary") or hero.get("subtitle") or ""
        event_data["excerpt"] = event_data.get("excerpt") or hero.get("subtitle") or hero.get("summary") or ""

def _ensure_beat(story: dict[str, Any], beat_type: str, title: str) -> dict[str, Any]:
    beats = story.setdefault("beats", [])
    for beat in beats:
        if isinstance(beat, dict) and beat.get("type") == beat_type:
            beat.setdefault("title", title)
            beat.setdefault("blocks", [])
            return beat
    beat = {"type": beat_type, "title": title, "blocks": []}
    beats.append(beat)
    return beat

def _append_text_block(beat: dict[str, Any], body: str) -> None:
    body = str(body or "").strip()
    if not body:
        return
    existing = " ".join(str(block.get("body") or block.get("text") or "") for block in beat.get("blocks") or [])
    if body in existing:
        return
    beat.setdefault("blocks", []).append({"type": "text", "body": body})

def _complete_interaction_details(event_data: dict[str, Any]) -> None:
    for index, character in enumerate(event_data.get("characters") or [], start=1):
        if not isinstance(character, dict):
            continue
        if not character.get("id"):
            character["id"] = f"nhan-vat-{index}"
        character["contribution"] = _first_text(character, "contribution", "description", "bio")
        character["description"] = _first_text(character, "description", "bio", "contribution")
        if isinstance(character.get("traits"), str):
            character["traits"] = [character["traits"]]

    for index, item in enumerate(event_data.get("timeline") or [], start=1):
        if not isinstance(item, dict):
            continue
        if not item.get("id"):
            item["id"] = f"moc-{index}"
        if not item.get("order"):
            item["order"] = index
        item["description"] = _first_text(item, "description", "detail", "longDescription", "summary")
        item["summary"] = _first_text(item, "summary", "description")
        points = item.get("keyPoints") or item.get("points") or item.get("facts") or item.get("bullets") or []
        item["keyPoints"] = [str(point).strip() for point in points if str(point).strip()] if isinstance(points, list) else []

    quiz = event_data.get("quiz")
    if isinstance(quiz, dict):
        event_data["quiz"] = quiz.get("questions") or []
    for index, question in enumerate(event_data.get("quiz") or [], start=1):
        if isinstance(question, dict) and not question.get("id"):
            question["id"] = f"cau-hoi-{index}"

def _complete_character_sides(event_data: dict[str, Any]) -> None:
    opponent = str(event_data.get("opponent") or "").lower()
    actors = [str(item).lower() for item in event_data.get("actors") or []]
    for index, character in enumerate(event_data.get("characters") or []):
        if not isinstance(character, dict):
            continue
        current = str(character.get("side") or "").strip().lower()
        if current in {"ally", "enemy"}:
            continue
        text_value = " ".join(
            str(character.get(key) or "")
            for key in ("name", "role", "bio", "faction", "contribution", "description")
        ).lower()
        if opponent and opponent in text_value:
            character["side"] = "enemy"
        elif any(actor and actor in text_value for actor in actors) or index == 0:
            character["side"] = "ally"
        else:
            character["side"] = "other"

def _complete_climax_scene(event_data: dict[str, Any]) -> None:
    story = event_data.get("story") or {}
    climax_beat = next((beat for beat in story.get("beats") or [] if beat.get("type") == "climax"), {})
    beat_title = str(climax_beat.get("title") or "Cao trào").strip()
    beat_body = _first_block_text(climax_beat)
    key_phases = event_data.get("keyPhases") or event_data.get("key_phases") or []
    tactical_map = event_data.get("tacticalMap") or event_data.get("tactical_map") or {}
    scene = event_data.get("climaxScene")
    if not isinstance(scene, dict):
        scene = {"title": beat_title, "phases": []}
        event_data["climaxScene"] = scene
    scene["title"] = str(scene.get("title") or beat_title).strip()
    scene["summary"] = _first_text(scene, "summary", "description") or beat_body
    scene["description"] = _first_text(scene, "description", "summary") or beat_body
    phases = [phase for phase in scene.get("phases") or [] if isinstance(phase, dict)]
    if not phases and isinstance(key_phases, list):
        phases = [phase for phase in key_phases if isinstance(phase, dict)]
    if not phases:
        phases = [{"id": "giai-doan-1", "label": beat_title, "summary": beat_body, "description": beat_body}]
    for index, phase in enumerate(phases, start=1):
        if not phase.get("id"):
            phase["id"] = f"giai-doan-{index}"
        phase["label"] = str(phase.get("label") or phase.get("title") or beat_title).strip()
        summary = str(phase.get("summary") or phase.get("description") or beat_body).strip()
        phase["summary"] = summary
        phase["description"] = str(phase.get("description") or summary).strip()
        if phase.get("importantDetail") and not phase.get("keyDetail"):
            phase["keyDetail"] = phase["importantDetail"]
    scene["phases"] = phases
    if isinstance(tactical_map, dict):
        scene["mapTitle"] = tactical_map.get("title") or scene.get("mapTitle")
        scene["mapDescription"] = tactical_map.get("description") or scene.get("mapDescription")
        points = tactical_map.get("points") or tactical_map.get("hotspots") or []
        if points and not scene.get("hotspots"):
            scene["hotspots"] = [
                _hotspot_from_point(point, index)
                for index, point in enumerate(points, start=1)
                if isinstance(point, dict)
            ]

def _hotspot_from_point(point: dict[str, Any], index: int) -> dict[str, Any]:
    position = point.get("position") if isinstance(point.get("position"), dict) else {}
    default_x = 18 + ((index - 1) % 4) * 20
    default_y = 28 + ((index - 1) // 4) * 22
    return {
        "id": str(point.get("id") or f"diem-{index}"),
        "x": float(position.get("x") or point.get("x") or min(default_x, 82)),
        "y": float(position.get("y") or point.get("y") or min(default_y, 78)),
        "label": str(point.get("label") or point.get("name") or f"Điểm {index}"),
        "name": point.get("name"),
        "description": str(point.get("description") or ""),
        "tacticalRole": point.get("tacticalRole") or point.get("role"),
    }

def _first_block_text(beat: dict[str, Any]) -> str:
    for block in beat.get("blocks") or []:
        if isinstance(block, dict):
            text_value = block.get("body") or block.get("text") or block.get("description") or block.get("quote") or block.get("caption")
            if text_value:
                return str(text_value).strip()
    return ""

def _first_text(source: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = source.get(key)
        text = _join_values(value)
        if text:
            return text
    return ""

def _join_values(*values: Any) -> str:
    parts: list[str] = []
    for value in values:
        if isinstance(value, list):
            parts.extend(str(item).strip() for item in value if str(item).strip())
        elif isinstance(value, str) and value.strip():
            parts.append(value.strip())
    return "\n\n".join(parts)

def _timeline_date_label(item: dict[str, Any]) -> str:
    parts = [str(item.get("day") or "").strip(), str(item.get("month") or "").strip(), str(item.get("year") or "").strip()]
    return "/".join(part for part in parts if part)

def _coverage_report(event_data: dict[str, Any]) -> dict[str, Any]:
    story = event_data.get("story") or {}
    checks = {
        "summary": bool(event_data.get("summary")),
        "excerpt": bool(event_data.get("excerpt")),
        "actors": bool(event_data.get("actors")),
        "characters": len(event_data.get("characters") or []) >= 1,
        "timeline": len(event_data.get("timeline") or []) >= 3,
        "storyBeats": len(story.get("beats") or []) >= 6,
        "quiz": len(event_data.get("quiz") or []) >= 3,
    }
    missing = [key for key, passed in checks.items() if not passed]
    return {"checks": checks, "missing": missing, "passed": not missing}
