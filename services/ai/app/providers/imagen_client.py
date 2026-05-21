import asyncio
import logging
import os
import uuid
from typing import Optional

import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

logger = logging.getLogger(__name__)


class ImagenClient:
    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model: str = "imagen-3.0-generate-001",
        backup_models: str = "",
    ):
        if not project_id:
            raise ValueError("GOOGLE_PROJECT_ID is required for ImagenClient")

        self.model_names = _model_names(model, backup_models)
        self.models: dict[str, ImageGenerationModel] = {}
        self.model = None
        self.last_model_name: str | None = None
        self.last_error: str | None = None

        try:
            vertexai.init(project=project_id, location=location)
            for model_name in self.model_names:
                try:
                    self.models[model_name] = ImageGenerationModel.from_pretrained(model_name)
                except Exception as e:
                    logger.error("Failed to load Imagen model %s: %s", model_name, e)
            self.model_names = [name for name in self.model_names if name in self.models]
            self.model = self.models[self.model_names[0]] if self.model_names else None
            logger.info(
                "Initialized Vertex AI ImagenClient for project=%s models=%s",
                project_id,
                ", ".join(self.model_names) or "(none)",
            )
        except Exception as e:
            logger.error("Failed to init Vertex AI: %s. Check GOOGLE_APPLICATION_CREDENTIALS", e)
            self.model = None

    def _generate_sync(self, prompt: str, aspect_ratio: str, model_name: str) -> Optional[str]:
        """Synchronous image generation + save. Runs in thread pool."""
        model = self.models[model_name]
        response = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio=aspect_ratio,
            safety_filter_level="block_few",
            person_generation="allow_adult",
        )

        if not response.images:
            logger.warning("Imagen returned 0 images (safety filter?)")
            return None

        static_dir = os.path.join(os.getcwd(), "static", "images", "generated")
        os.makedirs(static_dir, exist_ok=True)

        filename = f"imagen-{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(static_dir, filename)
        response.images[0].save(output_path)
        logger.info("Saved image to %s with model=%s", output_path, model_name)

        return f"/api/ai/ai-generated/{filename}"

    async def generate_image(self, prompt: str, aspect_ratio: str = "16:9") -> Optional[str]:
        """Generate image using Imagen 3. Runs sync SDK in thread pool."""
        if not self.models:
            logger.error("Imagen model not initialized")
            return None

        self.last_error = None
        self.last_model_name = None
        loop = asyncio.get_event_loop()

        for index, model_name in enumerate(self.model_names):
            try:
                logger.info(
                    "Calling Imagen | model=%s | aspect=%s | prompt=%s",
                    model_name,
                    aspect_ratio,
                    prompt[:100],
                )
                url = await loop.run_in_executor(
                    None,
                    self._generate_sync,
                    prompt,
                    aspect_ratio,
                    model_name,
                )
                self.last_model_name = model_name
                if url:
                    return url
                self.last_error = "empty_response"
            except Exception as e:
                message = str(e)
                self.last_error = message
                self.last_model_name = model_name
                logger.error("Imagen generation failed with model=%s: %s", model_name, message)
                if not _is_quota_error(message):
                    return None
                if index + 1 < len(self.model_names):
                    logger.warning("Imagen quota exceeded for model=%s; trying backup model", model_name)
                else:
                    logger.warning("Imagen quota exceeded for model=%s; no backup model left", model_name)
                continue

        return None


def _model_names(primary: str, backups: str) -> list[str]:
    names = [primary, *(backups or "").split(",")]
    result = []
    for name in names:
        clean = name.strip()
        if clean and clean not in result:
            result.append(clean)
    return result


def _is_quota_error(message: str) -> bool:
    normalized = message.lower()
    return "429" in normalized or "quota" in normalized or "resource_exhausted" in normalized
