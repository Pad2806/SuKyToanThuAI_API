from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

class FlexibleModel(BaseModel):
    model_config = ConfigDict(extra="allow")

class Citation(FlexibleModel):
    sourceType: str = "official"
    sourceId: str | None = None
    title: str | None = None
    chunkId: str | None = None
    blockId: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

class RenderAsset(FlexibleModel):
    slot: str
    assetType: str = "image"
    prompt: str | None = None
    publicUrl: str | None = None
    status: str = "queued"
    metadata: dict[str, Any] = Field(default_factory=dict)

class Character(FlexibleModel):
    id: str | None = None
    name: str
    role: str = ""
    side: str = "other"
    faction: str | None = None
    portrait: str | None = None
    bio: str = ""
    quote: str | None = None
    traits: list[str] | str = Field(default_factory=list)
    contribution: str = ""
    description: str = ""
    imagePrompt: str | None = None
    imageUrl: str | None = None

class TimelineMilestone(FlexibleModel):
    id: str | None = None
    order: int | None = None
    day: str = ""
    year: str = ""
    month: str = ""
    date: str = ""
    time: str | None = None
    title: str
    summary: str = ""
    description: str = ""
    keyPoints: list[str] = Field(default_factory=list)
    icon: str | None = None
    mood: str | None = None
    imagePrompt: str | None = None
    imageUrl: str | None = None

class ClimaxPhase(FlexibleModel):
    id: str | None = None
    label: str
    summary: str = ""
    description: str = ""
    keyDetail: str | None = None
    image: str | None = None

class Hotspot(FlexibleModel):
    id: str | None = None
    x: float
    y: float
    label: str
    name: str | None = None
    description: str = ""
    role: str | None = None
    tacticalRole: str | None = None

class ClimaxSceneData(FlexibleModel):
    title: str
    summary: str = ""
    description: str = ""
    quote: str | None = None
    backgroundImage: str | None = None
    mapImage: str | None = None
    phaseImages: list[str] = Field(default_factory=list)
    phases: list[ClimaxPhase] = Field(default_factory=list)
    hotspots: list[Hotspot] = Field(default_factory=list)

class AftermathStat(FlexibleModel):
    label: str
    value: str
    sublabel: str | None = None

class ComparisonList(FlexibleModel):
    title: str
    items: list[str] = Field(default_factory=list)

class AftermathData(FlexibleModel):
    title: str
    description: str = ""
    consequences: list[str] = Field(default_factory=list)
    lessons: list[str] = Field(default_factory=list)
    historicalMeaning: str = ""
    imagePrompt: str | None = None
    imageUrl: str | None = None
    stats: list[AftermathStat] = Field(default_factory=list)
    before: ComparisonList | None = None
    after: ComparisonList | None = None

class TakeawayData(FlexibleModel):
    happened: str = ""
    whyItMatters: str = ""
    lesson: str = ""

class QuizQuestion(FlexibleModel):
    id: str | None = None
    question: str
    options: list[str] = Field(default_factory=list)
    correct: int = 0
    explanation: str = ""

class ContentBlock(FlexibleModel):
    type: str
    body: str | None = None
    text: str | None = None
    description: str | None = None
    quote: str | None = None
    source: str | None = None
    image: str | None = None
    caption: str | None = None
    title: str | None = None
    items: list[Any] | None = None

class StoryBeat(FlexibleModel):
    type: Literal["hook", "setup", "rising", "climax", "falling", "takeaway"]
    title: str
    blocks: list[ContentBlock] = Field(default_factory=list)

class StoryData(FlexibleModel):
    templateType: str = "universal"
    beats: list[StoryBeat] = Field(default_factory=list)

class StoryEventData(FlexibleModel):
    id: str | None = None
    slug: str
    title: str
    eraId: str | None = None
    eraSlug: str | None = None
    year: int | None = None
    startYear: int | None = None
    endYear: int | None = None
    gradeTags: list[str] = Field(default_factory=list)
    topics: list[str] = Field(default_factory=list)
    type: str = "other"
    featured: bool = False
    summary: str = ""
    excerpt: str = ""
    image: str | None = None
    fallbackImage: str | None = None
    location: str | None = None
    actors: list[str] = Field(default_factory=list)
    opponent: str | None = None
    result: str | None = None
    characters: list[Character] = Field(default_factory=list)
    timeline: list[TimelineMilestone] = Field(default_factory=list)
    climaxScene: ClimaxSceneData | None = None
    aftermath: AftermathData | None = None
    takeaway: TakeawayData | None = None
    quiz: list[QuizQuestion] | dict[str, Any] = Field(default_factory=list)
    story: StoryData
    theme: str = "vietnamese-history"
    relatedEventSlugs: list[str] = Field(default_factory=list)

class StoryEventDraft(FlexibleModel):
    pageType: Literal["story-event"] = "story-event"
    flowType: Literal["system_data"] = "system_data"
    sourceMode: Literal["research"] = "research"
    title: str
    eventData: StoryEventData
    citations: list[Citation] = Field(default_factory=list)
    assets: list[RenderAsset] = Field(default_factory=list)
    coverageReport: dict[str, Any] = Field(default_factory=dict)
    moderation: dict[str, Any] = Field(default_factory=lambda: {"status": "approved", "reason": None})

def story_event_json_schema() -> dict[str, Any]:
    return StoryEventDraft.model_json_schema()

def normalize_story_event_envelope(value: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(value)
    normalized["pageType"] = "story-event"
    normalized["flowType"] = "system_data"
    normalized["sourceMode"] = "research"
    if "eventData" in normalized and isinstance(normalized["eventData"], dict):
        event_data = dict(normalized["eventData"])
        event_data.setdefault("theme", "vietnamese-history")
        normalized["eventData"] = event_data
    return normalized

def validate_story_event(value: str | dict[str, Any]) -> StoryEventDraft:
    if isinstance(value, str):
        return StoryEventDraft.model_validate_json(value)
    return StoryEventDraft.model_validate(value)
