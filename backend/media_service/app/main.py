# python -m uvicorn app.main:app --reload --port 8003
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
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.middleware.auth import AuthMiddleware
from app.routers import assets, search, slides, infographic

# ── Khởi tạo FastAPI app ──────────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Media Service — Tìm kiếm và tạo hình ảnh lịch sử bằng AI",
    docs_url="/docs",       # Swagger UI: http://localhost:8003/docs
    redoc_url="/redoc",     # ReDoc UI: http://localhost:8003/redoc
)

# ── Đăng ký Middleware ────────────────────────────────────────────────────────
# ⚠️ Starlette xử lý middleware theo thứ tự NGƯỢC: middleware add SAU sẽ chạy TRƯỚC.
# → CORSMiddleware phải được add CUỐI CÙNG để nó là lớp ngoài cùng,
#   xử lý OPTIONS preflight TRƯỚC khi AuthMiddleware can thiệp.

# Phase 1: is_enabled=False (chỉ log, không chặn request)
# Phase 3+: Đổi thành is_enabled=True để bắt buộc xác thực
app.add_middleware(AuthMiddleware, is_enabled=False)

# CORS — cho phép FE (localhost:5173) gọi API
# ⚠️ PHẢI add SAU AuthMiddleware → chạy TRƯỚC AuthMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",    # Vite dev server
        "http://localhost:3000",    # Fallback
        "http://localhost:8000",    # Nginx gateway
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Đăng ký Exception Handlers ───────────────────────────────────────────────
register_exception_handlers(app)

# ── Đăng ký Routers ──────────────────────────────────────────────────────────
app.include_router(assets.router)   # POST /api/v1/media/generate-assets
app.include_router(search.router)   # GET  /api/v1/media/categories, /search, ...
app.include_router(slides.router)   # POST /api/v1/media/generate-pptx
app.include_router(infographic.router)  # POST /api/v1/media/infographic-images


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
def health():
    """Kiểm tra service còn sống không — dùng bởi Docker + Nginx."""
    return {"status": "ok", "service": settings.PROJECT_NAME, "version": settings.VERSION}
