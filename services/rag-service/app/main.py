"""RAG Service — FastAPI app."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import config
from shared.logging import setup_logging

log = setup_logging("rag-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("RAG service starting...")
    yield
    log.info("RAG service shutting down...")


app = FastAPI(
    title="SuKyAI — RAG Service",
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
    return {"status": "ok", "service": "rag-service"}


# Routers (uncomment as implemented)
# from app.api import documents, retrieval
# app.include_router(documents.router, prefix="/api/v1")
# app.include_router(retrieval.router, prefix="/api/v1")
