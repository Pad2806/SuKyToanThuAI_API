from common.config.settings import get_settings


class VertexEmbeddingClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.settings.ai_provider != "vertex":
            raise RuntimeError("Official admin AI pipeline requires Vertex AI")
        if not self.settings.google_cloud_project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is required for Vertex AI embeddings")
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
        response = await client.aio.models.embed_content(
            model=self.settings.ai_embedding_model,
            contents=texts,
            config=types.EmbedContentConfig(output_dimensionality=1024),
        )
        return [list(item.values) for item in response.embeddings or []]
