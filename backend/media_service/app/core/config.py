"""
core/config.py
Tải toàn bộ biến môi trường từ file .env cho Media Service.
Đây là nơi duy nhất trong cả service được phép đọc .env.
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Trỏ tới file .env nằm ở thư mục backend/ (3 cấp cha lên từ file này)
# core/config.py → app/ → media_service/ → backend/.env
BACKEND_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Thông tin service ────────────────────────────────────────────
    PROJECT_NAME: str = "Media Service"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # ── Database ─────────────────────────────────────────────────────
    DATABASE_URL: str | None = None
    SUPABASE_URL: str | None = None

    # ── AI / LLM ─────────────────────────────────────────────────────
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Model mặc định

    # ── Wikimedia ─────────────────────────────────────────────────────
    WIKIMEDIA_API_URL: str = "https://commons.wikimedia.org/w/api.php"
    WIKIMEDIA_USER_AGENT: str = "SuKyToanThuAI/1.0 (contact@example.com)"

    # ── Cài đặt lọc ảnh ──────────────────────────────────────────────
    IMAGE_MIN_WIDTH: int = 800   # Chiều rộng tối thiểu (px)
    IMAGE_MIN_HEIGHT: int = 600  # Chiều cao tối thiểu (px)

    @property
    def resolved_database_url(self) -> str:
        """Ưu tiên DATABASE_URL, fallback sang SUPABASE_URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        if self.SUPABASE_URL:
            return self.SUPABASE_URL
        raise ValueError("Thiếu DATABASE_URL hoặc SUPABASE_URL trong file .env")


# Singleton dùng chung toàn service — import từ đây thay vì tạo lại
settings = Settings()
