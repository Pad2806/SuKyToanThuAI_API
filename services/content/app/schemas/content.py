from pydantic import BaseModel, ConfigDict


def to_camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class EraResponse(CamelModel):
    id: str
    slug: str
    name: str
    year_range: str
    start_year: int | None
    end_year: int | None
    summary: str
    cover_image: str | None
    fallback_image: str | None
    order: int
    featured_event_ids: list[str]


class EventResponse(CamelModel):
    id: str
    slug: str
    title: str
    era_id: str
    era_slug: str
    year: int
    grade_tags: list[str]
    type: str
    featured: bool
    summary: str
    excerpt: str
    image: str


class GradeResponse(CamelModel):
    id: str
    tag: str
    label: str
    order: int

