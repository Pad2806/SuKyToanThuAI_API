from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import eras, events, grades, internal, search, textbook

app = FastAPI(title="SuKyAI Content Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "content", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "service": "content",
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
    }


app.include_router(eras.router)
app.include_router(events.router)
app.include_router(grades.router)
app.include_router(textbook.router)
app.include_router(search.router)
app.include_router(internal.router)
