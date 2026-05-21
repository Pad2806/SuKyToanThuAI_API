from datetime import UTC, datetime
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import creator, pages, research

app = FastAPI(title="SuKyAI AI Service", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve AI-generated images as static files (under /ai-generated/ to avoid conflict with frontend public/images/)
static_dir = os.path.join(os.getcwd(), "static", "images", "generated")
os.makedirs(static_dir, exist_ok=True)
app.mount("/ai-generated", StaticFiles(directory=static_dir), name="generated-images")


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "ai", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "service": "ai",
        "status": "ok",
        "timestamp": datetime.now(UTC).isoformat(),
    }


app.include_router(research.router)
app.include_router(creator.router)
app.include_router(pages.router)
