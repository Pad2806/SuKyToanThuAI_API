from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class PageSummary(BaseModel):
    id: UUID
    title: str
    flowType: str
    sourceMode: str | None
    template: str | None
    status: str
    createdAt: datetime
    thumbnail: str | None = None
    coverageSummary: dict[str, Any] = {}


class PageDetail(PageSummary):
    renderPayload: dict[str, Any]
