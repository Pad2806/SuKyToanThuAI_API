"""
db/session.py
Khởi tạo kết nối cơ sở dữ liệu PostgreSQL (Supabase) bằng SQLAlchemy.
Cung cấp hàm get_db() để inject vào các endpoint qua Depends().
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Import settings từ core/ (không dùng db/config.py nữa)
from app.core.config import settings


class Base(DeclarativeBase):
    """Base class cho tất cả SQLAlchemy ORM model (nếu dùng sau này)."""
    pass


engine = create_engine(
    settings.resolved_database_url,
    pool_pre_ping=True,   # Tự kiểm tra kết nối còn sống không trước khi dùng
    pool_size=5,          # Số kết nối tối đa trong pool
    max_overflow=10,      # Cho phép tạo thêm tối đa 10 kết nối khi pool đầy
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    class_=Session,
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency cho FastAPI — inject DB session vào mỗi request.
    Session tự động đóng sau khi request kết thúc (finally block).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
