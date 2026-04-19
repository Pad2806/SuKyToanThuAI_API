from fastapi import FastAPI
from .router import router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Media Service", version=settings.VERSION, openapi_url=f"{settings.API_V1_STR}/media/openapi.json", docs_url=f"{settings.API_V1_STR}/media/docs")

app.include_router(router, prefix=f"{settings.API_V1_STR}/media", tags=["Media Service"])

@app.get("/health")
def health():
    return {"service": "Media", "status": "ok"}
