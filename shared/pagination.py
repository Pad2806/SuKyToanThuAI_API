"""Shared pagination helpers."""
from pydantic import BaseModel


class PageMeta(BaseModel):
    page: int
    page_size: int
    total: int | None = None


def paginate(page: int, page_size: int) -> tuple[int, int]:
    """Returns (offset, limit)."""
    offset = (max(1, page) - 1) * page_size
    return offset, page_size
