"""Story Service — FastAPI entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings

app = FastAPI(title="SuKyAI — Story Service", version="1.0.0",
              docs_url="/docs" if settings.DEBUG else None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"service": "story", "status": "ok"}


# Routers
from app.api.v1 import story_versions, images, review  # noqa: E402
app.include_router(story_versions.router, prefix=settings.API_PREFIX)
app.include_router(images.router,         prefix=settings.API_PREFIX)
app.include_router(review.router,         prefix=settings.API_PREFIX)
