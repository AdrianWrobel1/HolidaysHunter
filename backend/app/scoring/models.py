"""Domain models for unified scoring, value engine, confidence, and ranking."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class RankingProfile(StrEnum):
    BEST_DEALS = "best_deals"
    BEST_VALUE = "best_value"
    BUDGET = "budget"
    LUXURY = "luxury"
    FAMILY = "family"
    BEACH = "beach"
    LAST_MINUTE = "last_minute"


class ComponentResult(BaseModel):
    """Result produced by an individual scoring component."""

    name: str
    label: str
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1.0)
    weighted_score: float
    impact: float = Field(description="Net points contributed or subtracted from the aggregated score")
    explanation: str
    min_possible: float = 0.0
    max_possible: float = 100.0


class HotelRating(BaseModel):
    """Presentation model for hotel verified ratings."""

    guest_rating: float | None = None  # e.g. 8.6 / 10
    stars: float | None = None          # e.g. 4.0 / 5
    label: str = "Hotel Rating"


class PriceEfficiency(BaseModel):
    """Price efficiency metric."""

    daily_rate: float
    person_daily_rate: float
    market_avg_person_daily_rate: float
    efficiency_score: float = Field(ge=0, le=100)
    summary: str


class MarketPosition(BaseModel):
    """Market position metric."""

    cheaper_than_pct: float
    more_expensive_than_pct: float
    price_percentile: float
    rank_position: int
    total_candidates: int
    summary: str


class ValueScore(BaseModel):
    """Value Engine aggregated result."""

    total_score: int = Field(ge=0, le=100)
    raw_score: float
    summary: str
    components: list[ComponentResult] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)


class ConfidenceScore(BaseModel):
    """Confidence score metric representing data certainty."""

    score: float = Field(ge=0, le=100)  # 0 to 100%
    level: str = "MEDIUM"                 # "HIGH", "MEDIUM", "LOW"
    data_points_count: int = 0
    has_price_history: bool = False
    completeness_pct: float = 0.0
    explanations: list[str] = Field(default_factory=list)


class DealScore(BaseModel):
    """Deal Score primary purchasing attractiveness result."""

    total_score: int = Field(ge=0, le=100)
    raw_score: float
    summary: str
    value_score: float
    confidence: ConfidenceScore
    components: list[ComponentResult] = Field(default_factory=list)
    explanations: list[str] = Field(default_factory=list)
    diagnostic_details: dict[str, Any] = Field(default_factory=dict)


class RankedOffer(BaseModel):
    """Wrapper for an offer with its profile-specific rank and score."""

    offer_id: str | None = None
    offer_object: Any = None
    rank: int
    profile: RankingProfile
    score: float
    deal_score: int
    value_score: int
    confidence_pct: float
    rank_explanation: str
