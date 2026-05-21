from typing import Any

from common.config.settings import get_settings


class ImagenClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate_image(
        self,
        prompt: str,
        *,
        negative_prompt: str | None = None,
        person_generation: str | None = None,
        enhance_prompt: bool | None = None,
        aspect_ratio: str | None = None,
    ) -> bytes:
        if not self.settings.google_cloud_project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is required for Imagen")
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
        try:
            response = await client.aio.models.generate_images(
                model=self.settings.ai_image_model,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    include_rai_reason=True,
                    negative_prompt=negative_prompt,
                    person_generation=person_generation,
                    enhance_prompt=enhance_prompt,
                    aspect_ratio=aspect_ratio,
                ),
            )
            return _image_bytes(response)
        except RuntimeError:
            raise
        except Exception as exc:
            message = _safe_error(exc)
            if _is_quota_error(message):
                raise RuntimeError(
                    "Imagen quota exceeded for this project/model/region. "
                    "Google Cloud credits do not increase Vertex AI per-model quotas; wait for quota reset, reduce concurrent image generation, or request a quota increase for imagen-3.0-generate."
                ) from exc
            raise RuntimeError(f"Imagen generation failed: {message}") from exc

def _image_bytes(response: Any) -> bytes:
    generated = getattr(response, "generated_images", None) or []
    if not generated:
        reason = _rai_reason(response)
        suffix = f": {reason}" if reason else ""
        raise RuntimeError(f"Imagen did not return an image{suffix}")

    image = getattr(generated[0], "image", None)
    image_bytes = getattr(image, "image_bytes", None)
    if image_bytes:
        return image_bytes

    reason = _rai_reason(generated[0]) or _rai_reason(response)
    suffix = f": {reason}" if reason else ""
    raise RuntimeError(f"Imagen returned an image but no bytes were found{suffix}")

def _rai_reason(value: Any) -> str:
    for name in ("rai_filtered_reason", "raiFilteredReason", "rai_reason", "raiReason"):
        reason = getattr(value, name, None)
        if reason:
            return _safe_error(reason)
    return ""

def _safe_error(value: Any, limit: int = 240) -> str:
    text = str(getattr(value, "message", None) or value or value.__class__.__name__)
    text = " ".join(text.split())
    return f"{text[:limit].rstrip()}..." if len(text) > limit else text

def _is_quota_error(message: str) -> bool:
    lowered = message.lower()
    return "quota exceeded" in lowered or "online_prediction_requests_per_base_model" in lowered
