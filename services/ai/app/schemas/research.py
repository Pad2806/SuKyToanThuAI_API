from pydantic import BaseModel, Field


class ResearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    template: str = "universal"


class ResearchResponse(BaseModel):
    id: str
    title: str
    status: str | None = None
    renderPayload: dict | None = None
