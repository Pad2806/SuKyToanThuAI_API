from typing import Any, Literal

from pydantic import Field

from app.schemas.content import CamelModel

EventStatus = Literal["draft", "review", "published", "archived"]
SlotStatus = Literal[
    "missing",
    "prompted",
    "queued",
    "generated",
    "approved",
    "rejected",
    "failed",
    "archived",
]


class EventCreate(CamelModel):
    title: str = Field(min_length=2, max_length=180)
    slug: str = Field(min_length=2, max_length=180)
    era_id: str = "unknown"
    era_slug: str = "unknown"
    year: int = 0
    type: str = "other"
    template_type: str = "universal"
    summary: str = ""


class EventFactsUpdate(CamelModel):
    title: str | None = None
    slug: str | None = None
    era_id: str | None = None
    era_slug: str | None = None
    year: int | None = None
    start_year: int | None = None
    end_year: int | None = None
    grade_tags: list[str] | None = None
    type: str | None = None
    template_type: str | None = None
    summary: str | None = None
    excerpt: str | None = None
    image: str | None = None
    fallback_image: str | None = None
    location: str | None = None
    actors: list[str] | None = None
    opponent: str | None = None
    result: str | None = None
    theme: str | None = None
    related_event_slugs: list[str] | None = None


class StoryUpdate(CamelModel):
    story: dict[str, Any]
    generation_metadata: dict[str, Any] = Field(default_factory=dict)


class InteractionsUpdate(CamelModel):
    characters: list[dict[str, Any]] = Field(default_factory=list)
    timeline: list[dict[str, Any]] = Field(default_factory=list)
    climax_scene: dict[str, Any] | None = None
    aftermath: dict[str, Any] | None = None
    takeaway: dict[str, Any] | None = None
    quiz: list[dict[str, Any]] = Field(default_factory=list)


class AssetSlotUpsert(CamelModel):
    slot_key: str
    slot_label: str
    status: SlotStatus = "missing"
    prompt: str | None = None
    image_url: str | None = None
    gcs_uri: str | None = None
    review_notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssetReview(CamelModel):
    status: Literal["approved", "rejected"]
    review_notes: str | None = None


class LessonAssign(CamelModel):
    lesson_id: str | None = None


class SourceImportRequest(CamelModel):
    title: str = Field(min_length=2, max_length=240)
    text: str | None = None
    source_type: str = "reference"
    publisher: str | None = None
    source_url: str | None = None
    edition_year: int | None = None
    page_from: int | None = None
    page_to: int | None = None
    grade_tags: list[str] = Field(default_factory=list)


class DraftRequest(CamelModel):
    source_ids: list[str] = Field(default_factory=list)
    query: str | None = None


class QualityIssue(CamelModel):
    key: str
    label: str
    reason: str


class QualityReport(CamelModel):
    passed: bool
    score: int
    blocking_issues: list[QualityIssue] = Field(default_factory=list)
    warnings: list[QualityIssue] = Field(default_factory=list)
    requirements: dict[str, bool] = Field(default_factory=dict)
