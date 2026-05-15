from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PageSummary(BaseModel):
    id: UUID
    title: str
    content: str
    sources: list[str]
    template: str | None
    flowType: str
    status: str
    createdAt: datetime


class PageDetail(PageSummary):
    pass

