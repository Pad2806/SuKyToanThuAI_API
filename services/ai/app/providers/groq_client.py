import json
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"


class GroqClient:
    """Groq OpenAI-compatible client for lightweight tasks (keyword extraction)."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile"):
        if not api_key:
            raise ValueError("GROQ_API_KEY is required for GroqClient")
        self.model = model
        self._client = httpx.AsyncClient(
            base_url=_GROQ_BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )
        logger.info("Initialized GroqClient with model: %s", self.model)

    async def chat_json(self, messages: list[dict[str, str]]) -> dict[str, Any] | None:
        """Send chat request and parse JSON response."""
        body = {
            "model": self.model,
            "messages": messages,
            "response_format": {"type": "json_object"},
            "temperature": 0.3,
        }
        try:
            response = await self._client.post("/chat/completions", json=body)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except httpx.HTTPStatusError as e:
            logger.error("Groq API HTTP error: %s — %s", e.response.status_code, e.response.text)
            raise
        except (KeyError, json.JSONDecodeError) as e:
            logger.error("Groq response parse error: %s", e)
            return None

    async def close(self) -> None:
        await self._client.aclose()


_groq_client: GroqClient | None = None


def get_groq_client() -> GroqClient:
    global _groq_client
    from app.config import settings
    if _groq_client is None:
        _groq_client = GroqClient(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
        )
    return _groq_client
