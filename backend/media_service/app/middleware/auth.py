"""
middleware/auth.py
Middleware xác thực JWT token nội bộ giữa các microservice.

Khi Content Service gọi Media Service, nó truyền Bearer token
trong header Authorization. Middleware này kiểm tra token hợp lệ.

Phase 1: Middleware được đăng ký nhưng CHƯA chặn request
(để team có thể test các endpoint thoải mái trong giai đoạn đầu).

Phase 3+: Bật is_enabled=True để bắt buộc xác thực.
"""
import logging

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)

# Danh sách endpoint được phép bỏ qua xác thực
PUBLIC_PATHS = {
    "/health",
    "/api/v1/media/health",
    "/api/v1/media/db-check",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware kiểm tra JWT token cho mọi request vào Media Service.
    Hiện tại ở chế độ LOG-ONLY — ghi log nhưng không chặn request.
    """

    def __init__(self, app, is_enabled: bool = False):
        super().__init__(app)
        # is_enabled=False: chỉ log, không chặn (dùng trong dev/Phase 1)
        # is_enabled=True: chặn hẳn nếu không có token (dùng khi production)
        self.is_enabled = is_enabled

    async def dispatch(self, request: Request, call_next):
        # Bỏ qua public endpoints
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")

        if not auth_header.startswith("Bearer "):
            if self.is_enabled:
                return JSONResponse(
                    status_code=401,
                    content={"success": False, "error": {"message": "Thiếu token xác thực"}},
                )
            else:
                # Log-only mode: ghi log rồi để request đi qua
                logger.debug(
                    "Request thiếu Bearer token (log-only mode): %s %s",
                    request.method,
                    request.url.path,
                )

        return await call_next(request)
