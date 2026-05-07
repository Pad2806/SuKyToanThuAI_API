from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth import router as auth_router

app = FastAPI(
    title="Auth Service",
    description="Authentication Service - Cổng vào hệ thống cho đồ án AI Slide Lịch Sử",
    version="1.0.0"
)

# CORS cho React Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Auth Service đang chạy thành công!",
        "docs": "/docs"
    }