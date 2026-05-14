"""Story Service — FastAPI app."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import config
from shared.logging import setup_logging

log = setup_logging("story-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Story service starting...")
    yield
    log.info("Story service shutting down...")


app = FastAPI(
    title="SuKyAI — Story Service",
    version="1.0.0",
    docs_url="/docs" if config.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "story-service"}


# Routers (uncomment as implemented)
# from app.api import story_versions, review_items, images
# app.include_router(story_versions.router, prefix="/api/v1")
# app.include_router(review_items.router,   prefix="/api/v1")
# app.include_router(images.router,         prefix="/api/v1")
