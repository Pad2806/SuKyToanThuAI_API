import json
import logging
from typing import Any

from app.config import settings
from app.rag.retriever import ChunkResult
from app.generation.research_llm_prompt import build_research_llm_messages

logger = logging.getLogger(__name__)


def _parse_and_validate(data: dict[str, Any] | None) -> dict[str, Any] | None:
    if not data or not isinstance(data, dict):
        logger.warning("[LLM] Response is not a dict: %s", type(data))
        return None
    if not data.get("title"):
        logger.warning("[LLM] Missing required field 'title' in response")
        return None
    # Check confidence — reject low-confidence (hallucinated) responses
    confidence = data.get("confidence", "high")
    if confidence == "low":
        coverage = data.get("data_coverage", "Không đủ dữ liệu")
        logger.warning("[LLM] Low confidence — rejecting response. Coverage: %s", coverage)
        return None
    # Ensure summary exists (fallback to excerpt or title)
    if not data.get("summary"):
        data["summary"] = data.get("excerpt") or data.get("title")
    logger.info("[LLM] Validation passed — title=%r confidence=%s", data["title"], confidence)
    return data


def _get_client():
    """Return Vertex AI Gemini client if available, fallback to Gemini AI Studio."""
    if settings.google_project_id:
        from app.providers.vertex_gemini_client import get_vertex_gemini_client
        logger.info("[LLM] Using Vertex AI Gemini (%s)", settings.vertex_gemini_model)
        return get_vertex_gemini_client()
    if settings.google_api_key:
        from app.providers.gemini_client import get_gemini_client
        logger.warning("[LLM] Vertex AI not configured — falling back to Gemini AI Studio")
        return get_gemini_client()
    return None


async def llm_transform_research(
    query: str, chunks: list[ChunkResult], template_key: str
) -> dict[str, Any] | None:
    """
    Call LLM to convert RAG chunks into StoryEvent JSON.
    Returns None if failed, caller should fallback to regex.
    """
    if not chunks:
        logger.warning("[LLM] No chunks provided, skipping LLM transform")
        return None

    client = _get_client()
    if client is None:
        logger.warning("[LLM] No LLM client available, skipping transform")
        return None

    messages = build_research_llm_messages(query, chunks, template_key)
    logger.info("[LLM] Calling LLM for query=%r with %d chunks", query, len(chunks))

    try:
        response_dict = await client.chat_json(messages=messages)
        if response_dict:
            logger.info("[LLM] Got response with keys: %s", list(response_dict.keys()))
        else:
            logger.warning("[LLM] LLM returned None/empty response")
        return _parse_and_validate(response_dict)
    except Exception as e:
        logger.error("[LLM] Transform failed: %s", e, exc_info=True)
        return None
