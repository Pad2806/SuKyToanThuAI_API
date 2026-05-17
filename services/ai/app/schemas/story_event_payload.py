from typing import Any, Literal

from pydantic import BaseModel, Field


class CoverageIssue(BaseModel):
    key: str
    label: str
    reason: str


class CoverageReport(BaseModel):
    missing: list[CoverageIssue] = Field(default_factory=list)
    omittedSections: list[str] = Field(default_factory=list)
    userAcceptedMissing: bool = False


class ModerationSummary(BaseModel):
    status: Literal["approved", "rejected", "needs_review"] = "approved"
    reason: str | None = None


class RenderAsset(BaseModel):
    slot: str
    assetType: str = "image"
    prompt: str | None = None
    publicUrl: str | None = None
    status: Literal["queued", "generated", "failed", "archived"] = "queued"
    metadata: dict[str, Any] = Field(default_factory=dict)


class Citation(BaseModel):
    sourceType: str
    sourceId: str
    title: str | None = None
    sourceRefType: str | None = None
    sourceRefId: str | None = None
    chunkId: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class StoryEventRenderPayload(BaseModel):
    pageType: Literal["story-event"] = "story-event"
    flowType: Literal["system_data", "custom_content"]
    sourceMode: Literal["research", "creator"]
    title: str
    eventData: dict[str, Any]
    citations: list[Citation] = Field(default_factory=list)
    assets: list[RenderAsset] = Field(default_factory=list)
    coverageReport: CoverageReport = Field(default_factory=CoverageReport)
    moderation: ModerationSummary = Field(default_factory=ModerationSummary)
