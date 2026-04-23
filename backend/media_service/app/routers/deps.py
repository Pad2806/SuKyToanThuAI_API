"""
routers/deps.py
Các dependency dùng chung cho tất cả router (inject qua Depends()).
Hiện tại: provide DB session.
Sau này có thể thêm: verify JWT token, rate limiting, ...
"""
from collections.abc import Generator

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

# Re-export get_db để các router chỉ cần import từ 1 chỗ (deps.py)
# Thay vì import trực tiếp từ db/session.py
__all__ = ["get_db", "DBSession"]

# Type alias tiện dùng trong router
DBSession = Depends(get_db)
