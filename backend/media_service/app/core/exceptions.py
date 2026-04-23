"""
core/exceptions.py
Định nghĩa các lỗi tùy chỉnh và exception handler toàn cục.
Khi có lỗi xảy ra ở bất kỳ đâu trong service, response trả về
sẽ luôn có chung 1 format JSON thống nhất.
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


# ── Custom Exception Classes ──────────────────────────────────────────────────

class MediaServiceError(Exception):
    """Lỗi cơ sở của Media Service — tất cả lỗi kế thừa từ đây."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class WikimediaError(MediaServiceError):
    """Lỗi khi gọi Wikimedia API (network, timeout, không tìm được ảnh)."""
    def __init__(self, message: str = "Không thể lấy ảnh từ Wikimedia"):
        super().__init__(message, status_code=502)


class AIServiceError(MediaServiceError):
    """Lỗi khi gọi Groq LLM API (sinh keyword thất bại)."""
    def __init__(self, message: str = "AI service tạm thời không phản hồi"):
        super().__init__(message, status_code=503)


class ImageNotFoundError(MediaServiceError):
    """Không tìm được ảnh phù hợp sau khi thử tất cả keyword."""
    def __init__(self, message: str = "Không tìm được ảnh phù hợp cho nội dung này"):
        super().__init__(message, status_code=404)


class ValidationError(MediaServiceError):
    """Request gửi lên không đúng định dạng."""
    def __init__(self, message: str = "Dữ liệu gửi lên không hợp lệ"):
        super().__init__(message, status_code=422)


# ── Helper: Format lỗi thống nhất ────────────────────────────────────────────

def _error_response(status_code: int, error_type: str, message: str) -> JSONResponse:
    """Tạo JSON response lỗi theo format chuẩn của toàn team."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "error": {
                "type": error_type,
                "message": message,
            },
        },
    )


# ── Exception Handlers (đăng ký vào app trong main.py) ───────────────────────

def register_exception_handlers(app: FastAPI) -> None:
    """
    Đăng ký tất cả exception handler vào FastAPI app.
    Gọi hàm này 1 lần trong main.py khi khởi tạo app.
    """

    @app.exception_handler(MediaServiceError)
    async def media_service_error_handler(
        request: Request, exc: MediaServiceError
    ) -> JSONResponse:
        return _error_response(
            status_code=exc.status_code,
            error_type=type(exc).__name__,
            message=exc.message,
        )

    @app.exception_handler(WikimediaError)
    async def wikimedia_error_handler(
        request: Request, exc: WikimediaError
    ) -> JSONResponse:
        return _error_response(502, "WikimediaError", exc.message)

    @app.exception_handler(AIServiceError)
    async def ai_service_error_handler(
        request: Request, exc: AIServiceError
    ) -> JSONResponse:
        return _error_response(503, "AIServiceError", exc.message)

    @app.exception_handler(ImageNotFoundError)
    async def image_not_found_handler(
        request: Request, exc: ImageNotFoundError
    ) -> JSONResponse:
        return _error_response(404, "ImageNotFoundError", exc.message)

    @app.exception_handler(Exception)
    async def generic_error_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Bắt tất cả lỗi không mong đợi — không lộ stack trace ra ngoài
        return _error_response(500, "InternalServerError", "Lỗi nội bộ server")
