from fastapi import FastAPI
from .router import router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Auth Service", version=settings.VERSION, openapi_url=f"{settings.API_V1_STR}/auth/openapi.json", docs_url=f"{settings.API_V1_STR}/auth/docs")

app.include_router(router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth Service"])

@app.get("/health")
def health():
    return {"service": "Auth", "status": "ok"}
