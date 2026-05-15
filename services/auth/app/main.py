from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, profile

app = FastAPI(title="SuKyAI Auth Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "auth", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "service": "auth",
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
    }


app.include_router(auth.router)
app.include_router(profile.router)
