from fastapi import FastAPI
from .router import router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Education Service", version=settings.VERSION, openapi_url=f"{settings.API_V1_STR}/education/openapi.json", docs_url=f"{settings.API_V1_STR}/education/docs")

app.include_router(router, prefix=f"{settings.API_V1_STR}/education", tags=["Education Service"])

@app.get("/health")
def health():
    return {"service": "Education", "status": "ok"}
