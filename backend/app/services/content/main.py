from fastapi import FastAPI
from .router import router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Content Service", version=settings.VERSION, openapi_url=f"{settings.API_V1_STR}/content/openapi.json", docs_url=f"{settings.API_V1_STR}/content/docs")

app.include_router(router, prefix=f"{settings.API_V1_STR}/content", tags=["Content Service"])

@app.get("/health")
def health():
    return {"service": "Content", "status": "ok"}
