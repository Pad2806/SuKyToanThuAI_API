"""
services/cache_service.py
In-memory cache cho kết quả search Wikimedia.

Tránh gọi Wikimedia API lặp lại cho cùng keyword.
Cache tự hết hạn sau TTL_SECONDS giây.

Lưu ý: Cache nằm trong RAM, mất khi restart server.
Nếu cần cache bền vững hơn → dùng Redis (Phase 5+).
"""
import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# Thời gian cache tồn tại (giây). Sau thời gian này, cache tự hết hạn.
TTL_SECONDS = 600  # 10 phút

# Dictionary lưu cache: { key: (value, timestamp) }
_cache: dict[str, tuple[Any, float]] = {}


def get(key: str) -> Any | None:
    """
    Lấy giá trị từ cache.

    Args:
        key: Khóa cache (VD: "wikimedia:Dien Bien Phu 1954")

    Returns:
        Giá trị đã cache, hoặc None nếu không có / đã hết hạn.
    """
    if key not in _cache:
        return None

    value, created_at = _cache[key]

    # Kiểm tra hết hạn
    if time.time() - created_at > TTL_SECONDS:
        logger.debug("Cache expired: %s", key)
        del _cache[key]
        return None

    logger.debug("Cache hit: %s", key)
    return value


def set(key: str, value: Any) -> None:
    """
    Lưu giá trị vào cache.

    Args:
        key: Khóa cache
        value: Giá trị cần lưu
    """
    _cache[key] = (value, time.time())
    logger.debug("Cache set: %s", key)


def clear() -> None:
    """Xóa toàn bộ cache."""
    _cache.clear()
    logger.info("Cache cleared")


def stats() -> dict:
    """Trả về thống kê cache (dùng cho debug/monitoring)."""
    now = time.time()
    active = sum(1 for _, (_, t) in _cache.items() if now - t <= TTL_SECONDS)
    return {
        "total_entries": len(_cache),
        "active_entries": active,
        "expired_entries": len(_cache) - active,
        "ttl_seconds": TTL_SECONDS,
    }
