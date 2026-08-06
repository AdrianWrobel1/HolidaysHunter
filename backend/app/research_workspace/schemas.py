"""Pydantic schemas for Research Workspace."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.offer_analyzer.models import OfferAnalysisReport


class SessionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class SessionResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    collections_count: int = 0
    items_count: int = 0


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = "indigo"


class CollectionResponse(BaseModel):
    id: str
    session_id: str
    name: str
    color: str
    created_at: datetime


class ItemCreate(BaseModel):
    session_id: str
    offer_url: str
    collection_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)
    force: bool = False


class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool
    existing_item_id: str | None = None
    existing_session_id: str | None = None
    existing_session_name: str | None = None
    is_in_current_session: bool = False


class ItemUpdate(BaseModel):
    is_pinned: bool | None = None
    collection_id: str | None = None
    tags: list[str] | None = None
    notes: list[str] | None = None


class ChangeDelta(BaseModel):
    metric: str
    old_value: Any
    new_value: Any
    diff_text: str
    is_positive: bool | None = None


class ChangeDetectionReport(BaseModel):
    item_id: str
    previous_analysis_id: str | None
    latest_analysis_id: str
    compared_at: datetime
    deltas: list[ChangeDelta]
    summary: str


class WorkspaceItemResponse(BaseModel):
    id: str
    session_id: str
    collection_id: str | None = None
    offer_url: str
    offer_id: str | None = None
    is_pinned: bool
    tags: list[str]
    notes: list[str]
    latest_report: OfferAnalysisReport | None = None
    history_count: int = 0
    change_detection: ChangeDetectionReport | None = None
    created_at: datetime
    updated_at: datetime


class SnapshotCreate(BaseModel):
    session_id: str
    name: str = Field(..., min_length=1, max_length=200)


class SnapshotResponse(BaseModel):
    id: str
    session_id: str
    name: str
    created_at: datetime
    items_snapshot_count: int


class MultiOfferCompareRequest(BaseModel):
    item_ids: list[str] = Field(..., min_length=2, max_length=6)


class ComparisonMatrixRow(BaseModel):
    label: str
    values: list[Any]
    best_indices: list[int] = Field(default_factory=list)


class MultiOfferCompareReport(BaseModel):
    item_ids: list[str]
    items: list[WorkspaceItemResponse]
    matrix: dict[str, ComparisonMatrixRow]
    best_overall_index: int
    best_value_index: int
    cheapest_index: int
    highest_standard_index: int
    upgrade_recommendation: str


class BatchItemsRequest(BaseModel):
    item_ids: list[str] = Field(..., min_length=1)
    target_session_id: str | None = None
