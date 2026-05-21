import logging
from typing import Any
from app.generation.story_event_normalizer import normalize_story_event_payload
from app.rag.retriever import ChunkResult
from app.workspace.story_event_payload import story_event_shell

logger = logging.getLogger(__name__)


def _get_client():
    """Return Vertex AI Gemini client if available, fallback to Gemini AI Studio."""
    from app.config import settings
    if settings.google_project_id:
        from app.providers.vertex_gemini_client import get_vertex_gemini_client
        logger.info("[ERA-LLM] Using Vertex AI Gemini (%s)", settings.vertex_gemini_model)
        return get_vertex_gemini_client()
    if settings.google_api_key:
        from app.providers.gemini_client import get_gemini_client
        logger.warning("[ERA-LLM] Vertex AI not configured — falling back to Gemini AI Studio")
        return get_gemini_client()
    return None


def _validate_era_timeline(data: dict[str, Any] | None) -> dict[str, Any] | None:
    """Validate era-timeline JSON structure."""
    if not data or not isinstance(data, dict):
        logger.warning("[ERA-LLM] Response is not a dict")
        return None
    if not data.get("title"):
        logger.warning("[ERA-LLM] Missing required field 'title'")
        return None
    if not data.get("eras") or not isinstance(data["eras"], list):
        logger.warning("[ERA-LLM] Missing or invalid 'eras' array")
        return None
    # Check confidence — reject low-confidence responses
    confidence = data.get("confidence", "high")
    if confidence == "low":
        coverage = data.get("data_coverage", "Không đủ dữ liệu")
        logger.warning("[ERA-LLM] Low confidence — rejecting. Coverage: %s", coverage)
        return None
    # Ensure type is era-timeline
    data["type"] = "era-timeline"
    # Ensure summary exists
    if not data.get("summary"):
        data["summary"] = data.get("title")
    logger.info("[ERA-LLM] Validation passed — title=%r, eras=%d, confidence=%s", data["title"], len(data["eras"]), confidence)
    return data


_GRADE_TITLE_MAP = {
    "TH": "Lịch Sử Tiểu Học",
    "THCS": "Lịch Sử Trung Học Cơ Sở",
    "THPT": "Lịch Sử Trung Học Phổ Thông",
}


def _fix_grade_title(llm_title: str, grade_filter: str | None) -> str:
    """Force-correct title for grade-based queries."""
    if not grade_filter:
        return llm_title
    # Specific class number
    if grade_filter.isdigit():
        return f"Chương Trình Lịch Sử Lớp {grade_filter}"
    # Level code
    mapped = _GRADE_TITLE_MAP.get(grade_filter.upper())
    if mapped:
        return mapped
    return llm_title


async def payload_from_era_timeline(
    query: str, chunks: list[ChunkResult], template_key: str, intent: dict | None = None
) -> dict[str, Any]:
    """Generate era-timeline payload using dedicated LLM prompt."""
    logger.info("[ERA-GEN] Building era-timeline payload for query=%r with %d chunks", query, len(chunks))

    client = _get_client()
    if client is None:
        logger.warning("[ERA-GEN] No LLM client available — falling back to regex")
        return _fallback_payload(query, chunks, template_key)

    if intent and intent.get("search_strategy") == "grade_based":
        from app.generation.grade_curriculum_llm_prompt import build_grade_curriculum_llm_messages
        messages = build_grade_curriculum_llm_messages(query, chunks, intent.get("grade_filter"))
    else:
        from app.generation.era_timeline_llm_prompt import build_era_timeline_llm_messages
        messages = build_era_timeline_llm_messages(query, chunks)

    try:
        result = await client.chat_json(messages=messages)
        validated = _validate_era_timeline(result)
        if validated:
            # Post-process: force-correct title for grade-based queries
            if intent and intent.get("search_strategy") == "grade_based":
                validated["title"] = _fix_grade_title(validated["title"], intent.get("grade_filter"))
            payload = story_event_shell(validated["title"], "era-timeline", "system_data", "research", validated.get("summary", ""))
            payload["eventData"].update(validated)
            payload["coverageReport"] = {"missing": [], "omittedSections": [], "userAcceptedMissing": False}
            payload["citations"] = [{"title": c.title, "chunkId": str(c.id)} for c in chunks]
            return normalize_story_event_payload(payload, validated["title"], "era-timeline", "system_data", "research")
    except Exception as e:
        logger.error("[ERA-GEN] LLM transform failed: %s", e, exc_info=True)

    logger.warning("[ERA-GEN] LLM failed — using fallback")
    return _fallback_payload(query, chunks, template_key)


def _fallback_payload(query: str, chunks: list[ChunkResult], template_key: str) -> dict[str, Any]:
    """Simple fallback when LLM is unavailable."""
    title = query.strip()[:80] or "Tổng quan lịch sử"
    summary = "\n".join(c.content[:200] for c in chunks[:3])
    payload = story_event_shell(title, "era-timeline", "system_data", "research", summary[:420])
    payload["eventData"]["eras"] = []
    payload["eventData"]["connections"] = []
    payload["eventData"]["overview"] = {"totalEvents": 0, "totalYears": 0, "highlight": "Không đủ dữ liệu"}
    payload["eventData"]["type"] = "era-timeline"
    payload["citations"] = [{"title": c.title, "chunkId": str(c.id)} for c in chunks]
    return normalize_story_event_payload(payload, title, "era-timeline", "system_data", "research")
