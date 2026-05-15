from pydantic import BaseModel, Field


class CreatorRequest(BaseModel):
    content: str = Field(min_length=1, max_length=12000)
    template: str = "universal"

