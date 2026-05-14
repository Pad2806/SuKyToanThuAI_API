"""Shared async HTTP client — internal service-to-service calls."""
import httpx

DEFAULT_TIMEOUT = 15.0


class ServiceClient:
    """Thin async HTTP wrapper for internal service calls."""

    def __init__(self, base_url: str, service_token: str = "", timeout: float = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token
        self.timeout = timeout

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.service_token:
            h["X-Service-Token"] = self.service_token
        return h

    async def get(self, path: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.get(f"{self.base_url}{path}", headers=self._headers(), **kwargs)

    async def post(self, path: str, json: dict, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.post(f"{self.base_url}{path}", json=json,
                                     headers=self._headers(), **kwargs)

    async def patch(self, path: str, json: dict, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await client.patch(f"{self.base_url}{path}", json=json,
                                      headers=self._headers(), **kwargs)
