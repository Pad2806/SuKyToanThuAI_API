"""Auth Service — FastAPI app."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import config
from shared.database import make_engine, make_session_factory
from shared.logging import setup_logging

log = setup_logging("auth-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Auth service starting...")
    yield
    log.info("Auth service shutting down...")


app = FastAPI(
    title="SuKyAI — Auth Service",
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
    return {"status": "ok", "service": "auth-service"}


# Routers (uncomment as implemented)
# from app.api.routes import router
# app.include_router(router, prefix="/api/v1")
