from fastapi import FastAPI
from .router import router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title="Workspace Service", version=settings.VERSION, openapi_url=f"{settings.API_V1_STR}/workspace/openapi.json", docs_url=f"{settings.API_V1_STR}/workspace/docs")

app.include_router(router, prefix=f"{settings.API_V1_STR}/workspace", tags=["Workspace Service"])

@app.get("/health")
def health():
    return {"service": "Workspace", "status": "ok"}
