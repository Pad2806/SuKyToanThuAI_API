"""
AI Provider Client — Adapter for 9router OpenAI-compatible API.

All configuration is read from environment variables:
  NINEROUTER_API_KEY    — API key for 9router
  NINEROUTER_BASE_URL   — Base URL (e.g. https://api.9router.ai/v1)
  LLM_MODEL             — LLM model name
  EMBEDDING_MODEL       — Embedding model name (default: intfloat/multilingual-e5-large)
  IMAGE_MODEL           — Image generation model name

Never hardcode credentials.
"""
import logging
from typing import Any

import httpx
from openai import AsyncOpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class AIProviderClient:
    """Async adapter wrapping 9router via OpenAI-compatible SDK."""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(
            api_key=settings.NINEROUTER_API_KEY,
            base_url=settings.NINEROUTER_BASE_URL,
        )

    async def generate_json(self, prompt: str, schema: dict[str, Any]) -> dict[str, Any]:
        """Call LLM and enforce JSON output matching schema."""
        response = await self._client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a Vietnamese history AI assistant. "
                        "Respond ONLY with valid JSON matching the given schema. "
                        "Do not fabricate historical facts — base output only on provided context."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        import json
        raw = response.choices[0].message.content or "{}"
        return json.loads(raw)

    async def generate_text(self, prompt: str) -> str:
        """Call LLM for plain text generation."""
        response = await self._client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
        )
        return response.choices[0].message.content or ""

    async def generate_image(self, prompt: str) -> str:
        """Generate an image and return the URL from the API response.

        Note: Caller is responsible for downloading and uploading to S3.
        """
        response = await self._client.images.generate(
            model=settings.IMAGE_MODEL,
            prompt=prompt,
            n=1,
            size="1024x1024",
        )
        return response.data[0].url or ""

    async def embed(self, text: str) -> list[float]:
        """Generate a 1024-dim embedding vector for the given text."""
        response = await self._client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text,
        )
        vector = response.data[0].embedding
        if len(vector) != 1024:
            raise ValueError(
                f"Embedding model returned {len(vector)} dims, expected 1024. "
                f"Check EMBEDDING_MODEL={settings.EMBEDDING_MODEL}"
            )
        return vector

    async def health_check(self) -> bool:
        """Ping the API to verify connectivity."""
        try:
            await self._client.models.list()
            return True
        except Exception as exc:
            logger.warning("AI provider health check failed: %s", exc)
            return False
