"""Content Service — FastAPI app."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import config
from shared.logging import setup_logging

log = setup_logging("content-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Content service starting...")
    yield
    log.info("Content service shutting down...")


app = FastAPI(
    title="SuKyAI — Content Service",
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
    return {"status": "ok", "service": "content-service"}


# Routers (uncomment as implemented)
# from app.api import events, eras, grades, lessons, topics
# app.include_router(events.router,  prefix="/api/v1")
# app.include_router(eras.router,    prefix="/api/v1")
# app.include_router(grades.router,  prefix="/api/v1")
# app.include_router(lessons.router, prefix="/api/v1")
# app.include_router(topics.router,  prefix="/api/v1")
