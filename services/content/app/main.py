"""Content Service — FastAPI entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.settings import settings

app = FastAPI(title="SuKyAI — Content Service", version="1.0.0",
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
    return {"service": "content", "status": "ok"}


# Routers
from app.api.v1 import eras, grades, topics, lessons, events  # noqa: E402
app.include_router(eras.router,    prefix=settings.API_PREFIX)
app.include_router(grades.router,  prefix=settings.API_PREFIX)
app.include_router(topics.router,  prefix=settings.API_PREFIX)
app.include_router(lessons.router, prefix=settings.API_PREFIX)
app.include_router(events.router,  prefix=settings.API_PREFIX)
