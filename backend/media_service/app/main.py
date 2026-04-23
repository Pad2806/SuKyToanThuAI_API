# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
Media Service — Entry Point
Port: 8003 (xem docker-compose.yml)
API Gateway: /api/v1/media/* (xem nginx.conf)

Cấu trúc thư mục (Phase 1):
    app/
    ├── ai/           ← Groq client + prompt templates
    ├── core/         ← Config (.env) + Custom exceptions
    ├── db/           ← Database session (SQLAlchemy)
    ├── middleware/   ← JWT auth middleware
    ├── models/       ← SQLAlchemy ORM models (Phase 3)
    ├── routers/      ← API endpoints (assets, search)
    ├── schemas/      ← Pydantic request/response models
    ├── services/     ← Business logic (wikimedia, filter, asset)
    ├── tasks/        ← Background workers
    └── utils/        ← Helper functions
"""
from fastapi import FastAPI

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.middleware.auth import AuthMiddleware
from app.routers import assets, search

# ── Khởi tạo FastAPI app ──────────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Media Service — Tìm kiếm và tạo hình ảnh lịch sử bằng AI",
    docs_url="/docs",       # Swagger UI: http://localhost:8003/docs
    redoc_url="/redoc",     # ReDoc UI: http://localhost:8003/redoc
)

# ── Đăng ký Middleware ────────────────────────────────────────────────────────
# Phase 1: is_enabled=False (chỉ log, không chặn request)
# Phase 3+: Đổi thành is_enabled=True để bắt buộc xác thực
app.add_middleware(AuthMiddleware, is_enabled=False)

# ── Đăng ký Exception Handlers ───────────────────────────────────────────────
register_exception_handlers(app)

# ── Đăng ký Routers ──────────────────────────────────────────────────────────
app.include_router(assets.router)   # POST /api/v1/media/generate-assets
app.include_router(search.router)   # GET  /api/v1/media/categories, /search, ...


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():
    """Kiểm tra service còn sống không — dùng bởi Docker + Nginx."""
    return {"status": "ok", "service": settings.PROJECT_NAME, "version": settings.VERSION}
