from typing import Any

import httpx


class OpenAIClient:
    def __init__(self, api_key: str, base_url: str, timeout: float = 60.0) -> None:
        self._client = httpx.AsyncClient(
            base_url=base_url.rstrip("/"),
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=timeout,
        )

    async def embed(self, texts: list[str], model: str) -> list[list[float]]:
        response = await self._client.post(
            "/embeddings",
            json={"model": model, "input": texts},
        )
        response.raise_for_status()
        payload = response.json()
        return [item["embedding"] for item in payload["data"]]

    async def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        body: dict[str, Any] = {"model": model, "messages": messages}
        if response_format:
            body["response_format"] = response_format
        response = await self._client.post("/chat/completions", json=body)
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"]

    async def close(self) -> None:
        await self._client.aclose()

