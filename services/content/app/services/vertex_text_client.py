import json
from typing import Any

from common.config.settings import get_settings


class VertexTextClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate_json(self, prompt: str, schema: dict[str, Any], model: str | None = None) -> dict[str, Any]:
        if self.settings.ai_provider != "vertex":
            raise RuntimeError("Official admin AI pipeline requires Vertex AI")
        if not self.settings.google_cloud_project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is required for Vertex AI")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("google-genai is not installed") from exc

        client = genai.Client(
            vertexai=True,
            project=self.settings.google_cloud_project,
            location=self.settings.google_cloud_location,
        )
        response = await client.aio.models.generate_content(
            model=model or self.settings.ai_draft_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_json_schema=schema,
            ),
        )
        return json.loads(response.text or "{}")
