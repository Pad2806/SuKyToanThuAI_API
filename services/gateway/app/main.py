"""Gateway — FastAPI reverse proxy.

Forwards every /api/v1/* request to the appropriate upstream service.
Preserves method, headers, body, and returns downstream response as-is.
"""
import httpx
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import config
from app.routes import resolve_upstream

app = FastAPI(title="SuKyAI Gateway", version="1.0.0", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway"}


@app.api_route(
    "/api/v1/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
)
async def proxy(path: str, request: Request) -> Response:
    full_path = f"/api/v1/{path}"
    upstream = resolve_upstream(full_path)

    if upstream is None:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "ROUTE_NOT_FOUND", "message": f"No service mapped for {full_path}"}},
        )

    # Build upstream URL preserving query string
    target_url = f"{upstream}{full_path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    # Forward headers, strip host
    headers = dict(request.headers)
    headers.pop("host", None)

    body = await request.body()

    try:
        async with httpx.AsyncClient(timeout=config.GATEWAY_TIMEOUT) as client:
            upstream_response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
            )
        return Response(
            content=upstream_response.content,
            status_code=upstream_response.status_code,
            headers=dict(upstream_response.headers),
            media_type=upstream_response.headers.get("content-type", "application/json"),
        )
    except httpx.ConnectError:
        return JSONResponse(
            status_code=503,
            content={"error": {"code": "SERVICE_UNAVAILABLE", "message": f"Upstream service unavailable"}},
        )
    except httpx.TimeoutException:
        return JSONResponse(
            status_code=504,
            content={"error": {"code": "GATEWAY_TIMEOUT", "message": "Upstream service timed out"}},
        )
