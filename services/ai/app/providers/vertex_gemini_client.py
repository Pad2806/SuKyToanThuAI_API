import json
import logging
import os
import uuid
from typing import Any

import vertexai
from vertexai.generative_models import GenerationConfig, GenerativeModel

logger = logging.getLogger(__name__)


class VertexGeminiClient:
    """Vertex AI Gemini client for JSON generation (uses paid credit, no quota limit)."""

    def __init__(self, project_id: str, location: str, model: str = "gemini-2.5-flash"):
        if not project_id:
            raise ValueError("GOOGLE_PROJECT_ID is required for VertexGeminiClient")
        vertexai.init(project=project_id, location=location)
        self._model_name = model
        self._gen_config = GenerationConfig(
            temperature=0.4,
            response_mime_type="application/json",
        )
        logger.info("Initialized VertexGeminiClient with model: %s (project=%s)", model, project_id)

    def _convert_messages(self, messages: list[dict[str, str]]) -> tuple[str | None, list]:
        """Convert OpenAI-style messages to Vertex AI Gemini format."""
        system_text = None
        contents = []
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "system":
                system_text = (system_text + "\n\n" + content) if system_text else content
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
        return system_text, contents

    async def chat_json(self, messages: list[dict[str, str]]) -> dict[str, Any] | None:
        """Send chat request to Vertex AI Gemini and return parsed JSON."""
        system_text, contents = self._convert_messages(messages)

        model = GenerativeModel(
            self._model_name,
            system_instruction=system_text,
            generation_config=self._gen_config,
        )

        try:
            response = await model.generate_content_async(contents)
            logger.info("[VERTEX] Gemini response received, parsing JSON")
            return json.loads(response.text)
        except json.JSONDecodeError as e:
            logger.error("[VERTEX] JSON parse error: %s | raw: %s", e, response.text[:200])
            return None
        except Exception as e:
            logger.error("[VERTEX] Gemini API error: %s", e)
            raise


_vertex_gemini_client: VertexGeminiClient | None = None
_vertex_gemini_image_client: "VertexGeminiImageClient | None" = None


def get_vertex_gemini_client() -> VertexGeminiClient:
    global _vertex_gemini_client
    from app.config import settings
    if _vertex_gemini_client is None:
        _vertex_gemini_client = VertexGeminiClient(
            project_id=settings.google_project_id,
            location=settings.google_location,
            model=settings.vertex_gemini_model,
        )
    return _vertex_gemini_client


class VertexGeminiImageClient:
    """Vertex AI Gemini image client for Nano Banana fallback generation."""

    def __init__(self, project_id: str, location: str, model: str):
        if not project_id:
            raise ValueError("GOOGLE_PROJECT_ID is required for VertexGeminiImageClient")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("google-genai is required for Gemini image generation") from exc

        self._types = types
        self.model_name = model
        self.last_error: str | None = None
        self.last_model_name: str | None = None
        self.client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location,
        )
        logger.info(
            "Initialized VertexGeminiImageClient with model=%s project=%s location=%s",
            model,
            project_id,
            location,
        )

    def _generate_sync(self, prompt: str) -> str | None:
        logger.warning("Calling Gemini image | model=%s", self.model_name)
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=self._types.GenerateContentConfig(
                response_modalities=[self._types.Modality.IMAGE],
            ),
        )
        for part in response.candidates[0].content.parts:
            if not getattr(part, "inline_data", None):
                continue
            image_bytes = part.inline_data.data
            extension = _mime_extension(part.inline_data.mime_type)
            static_dir = os.path.join(os.getcwd(), "static", "images", "generated")
            os.makedirs(static_dir, exist_ok=True)
            filename = f"gemini-image-{uuid.uuid4().hex[:8]}.{extension}"
            output_path = os.path.join(static_dir, filename)
            with open(output_path, "wb") as image_file:
                image_file.write(image_bytes)
            logger.warning("Saved Gemini image to %s with model=%s", output_path, self.model_name)
            return f"/api/ai/ai-generated/{filename}"
        self.last_error = "empty_response"
        return None

    async def generate_image(self, prompt: str, aspect_ratio: str = "16:9") -> str | None:
        self.last_error = None
        self.last_model_name = self.model_name
        try:
            import asyncio

            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._generate_sync, prompt)
        except Exception as exc:
            self.last_error = str(exc)
            logger.error("Gemini image generation failed with model=%s: %s", self.model_name, exc)
            return None


def _mime_extension(mime_type: str | None) -> str:
    if mime_type == "image/jpeg":
        return "jpg"
    if mime_type == "image/webp":
        return "webp"
    return "png"


def get_vertex_gemini_image_client() -> VertexGeminiImageClient:
    global _vertex_gemini_image_client
    from app.config import settings

    if _vertex_gemini_image_client is None:
        _vertex_gemini_image_client = VertexGeminiImageClient(
            project_id=settings.google_project_id,
            location=settings.gemini_image_location,
            model=settings.gemini_image_model,
        )
    return _vertex_gemini_image_client
