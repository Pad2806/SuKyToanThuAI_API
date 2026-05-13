"""SuKyAI FastAPI Application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

app = FastAPI(
    title="Sử Ký Toàn Thư AI — API",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["infra"])
async def health():
    return {"status": "ok", "env": settings.APP_ENV}


# ── Routers (add as each is implemented) ────────────────────────────────
# from app.api.v1 import events, eras, topics, grades, admin
# app.include_router(events.router, prefix=settings.API_PREFIX)
# app.include_router(eras.router, prefix=settings.API_PREFIX)
# app.include_router(topics.router, prefix=settings.API_PREFIX)
# app.include_router(admin.router, prefix=settings.API_PREFIX + "/admin")
