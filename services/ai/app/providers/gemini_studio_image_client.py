import asyncio
import logging
import os
import uuid

logger = logging.getLogger(__name__)


class GeminiStudioImageClient:
    """Google AI Studio image client — uses API key (separate quota from Vertex AI)."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash-preview-05-20"):
        if not api_key:
            raise ValueError("API key is required for GeminiStudioImageClient")
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc:
            raise RuntimeError("google-genai is required for Gemini Studio image generation") from exc

        self._types = types
        self.model_name = model
        self.last_error: str | None = None
        self.last_model_name: str | None = None
        self.client = genai.Client(api_key=api_key)
        logger.info("Initialized GeminiStudioImageClient with model=%s", model)

    def _generate_sync(self, prompt: str) -> str | None:
        logger.warning("Calling Gemini Studio image | model=%s", self.model_name)
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
            filename = f"studio-image-{uuid.uuid4().hex[:8]}.{extension}"
            output_path = os.path.join(static_dir, filename)
            with open(output_path, "wb") as image_file:
                image_file.write(image_bytes)
            logger.warning("Saved Studio image to %s with model=%s", output_path, self.model_name)
            return f"/api/ai/ai-generated/{filename}"
        self.last_error = "empty_response"
        return None

    async def generate_image(self, prompt: str, aspect_ratio: str = "16:9") -> str | None:
        self.last_error = None
        self.last_model_name = self.model_name
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, self._generate_sync, prompt)
        except Exception as exc:
            self.last_error = str(exc)
            logger.error("Gemini Studio image generation failed with model=%s: %s", self.model_name, exc)
            return None


def _mime_extension(mime_type: str | None) -> str:
    if mime_type == "image/jpeg":
        return "jpg"
    if mime_type == "image/webp":
        return "webp"
    return "png"


_gemini_studio_image_client: GeminiStudioImageClient | None = None


def get_gemini_studio_image_client() -> GeminiStudioImageClient:
    global _gemini_studio_image_client
    from app.config import settings

    if _gemini_studio_image_client is None:
        _gemini_studio_image_client = GeminiStudioImageClient(
            api_key=settings.gemini_studio_api_key,
            model=settings.gemini_studio_image_model,
        )
    return _gemini_studio_image_client
