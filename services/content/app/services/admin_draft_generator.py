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
        payload["coverageReport"] = _coverage_report(payload.get("eventData") or {})
        payload["generationMetadata"] = {
            "provider": "vertex",
            "model": self.client.settings.ai_draft_model,
            "sourceIds": source_ids,
            "promptHash": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        }
        return {"status": "drafted", "payload": payload}


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
