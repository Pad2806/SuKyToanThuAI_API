from io import BytesIO

from common.config.settings import get_settings


class ImagenClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def generate_image(self, prompt: str) -> bytes:
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
        response = await client.aio.models.generate_images(
            model=self.settings.ai_image_model,
            prompt=prompt,
            config=types.GenerateImagesConfig(number_of_images=1, include_rai_reason=True),
        )
        if not response.generated_images:
            raise RuntimeError("Imagen did not return an image")
        image = response.generated_images[0].image
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return buffer.getvalue()
