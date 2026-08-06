"""Pydantic schemas for Offer Analyzer request and response report."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from pydantic import BaseModel, Field, HttpUrl


class OfferAnalyzeRequest(BaseModel):
    """Request payload for analyzing an offer URL."""

    url: str = Field(..., description="Full URL to the travel offer.")


class TargetOfferSummary(BaseModel):
    """Summary of the target offer being analyzed."""

    external_id: str
    provider: str
    title: str
    country: str
    region: str | None = None
    city: str | None = None
    hotel_name: str
    hotel_stars: float | None = None
    hotel_rating: float | None = None
    departure_date: date
    return_date: date
    duration_nights: int
    departure_city: str
    adults: int
    children: int = 0
    meal_type: str
    transport_type: str
    price_total: Decimal
    price_per_person: Decimal
    currency: str = "PLN"
    offer_url: str | None = None
    image_url: str | None = None


class SimilarOfferItem(BaseModel):
    """Single similar offer item with similarity score and explanation."""

    id: str | None = None
    external_id: str
    provider: str
    title: str
    hotel_name: str
    country: str
    region: str | None = None
    hotel_stars: float | None = None
    departure_date: date
    duration_nights: int
    meal_type: str
    departure_city: str
    price_per_person: Decimal
    similarity_score: float
    explanations: list[str]
    offer_url: str | None = None
    transport_type: str = "flight"


class SimilarityAnalysis(BaseModel):
    """Similarity analysis results."""

    candidates_count: int
    top_matches: list[SimilarOfferItem]


class PriceAnalysis(BaseModel):
    """Detailed price statistics and position of target offer."""

    min_price: float
    max_price: float
    mean_price: float
    median_price: float
    std_dev: float
    percentile_25: float
    percentile_75: float
    target_price: float
    price_per_day: float
    price_per_person_per_day: float
    price_diff_amount: float
    price_diff_pct: float
    position_summary: str


class MarketPosition(BaseModel):
    """Market position metrics."""

    cheaper_than_pct: float
    more_expensive_than_pct: float
    price_percentile: float
    rank_position: int
    total_candidates: int
    rank_summary: str


class PriceEfficiency(BaseModel):
    """Price efficiency metrics."""

    daily_rate: float
    person_daily_rate: float
    market_avg_person_daily_rate: float
    efficiency_score: float
    summary: str


class OfferQuality(BaseModel):
    """Offer quality metrics."""

    quality_score: float
    completeness_pct: float
    highlights: list[str]


class DealScoreComponentSchema(BaseModel):
    """Individual Deal Score component breakdown."""

    name: str
    score: float
    weight: float
    weighted_score: float
    impact: float = 0.0
    explanation: str | None = None


class DealScoreBreakdown(BaseModel):
    """Overall Deal Score result and components."""

    total_score: int
    raw_score: float
    summary: str
    value_score: float = 50.0
    confidence: dict[str, Any] = Field(default_factory=dict)
    components: list[DealScoreComponentSchema]
    explanations: list[str] = Field(default_factory=list)



class Recommendation(BaseModel):
    """Deterministic recommendation result."""

    verdict_badge: str
    verdict_color: str
    title: str
    takeaways: list[str]


class HistogramBin(BaseModel):
    """Bin for price histogram."""

    bin_label: str
    bin_min: float
    bin_max: float
    count: int
    is_target_bin: bool = False


class BoxPlotData(BaseModel):
    """Box plot metrics."""

    min_val: float
    q1: float
    median: float
    q3: float
    max_val: float
    target_val: float


class VisualizationData(BaseModel):
    """Pre-calculated chart data structures for frontend rendering."""

    histogram_bins: list[HistogramBin]
    box_plot: BoxPlotData
    deal_score_breakdown: list[dict[str, Any]]


class OfferAnalysisReport(BaseModel):
    """Complete, structured Offer Analysis Report."""

    analysis_id: str
    target_type: str = "offer"
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: float | None = None
    framework_version: str = "1.0.0"
    cache_used: bool = False

    target_offer: TargetOfferSummary
    similarity: SimilarityAnalysis
    statistics: PriceAnalysis
    market_position: MarketPosition
    price_efficiency: PriceEfficiency
    offer_quality: OfferQuality
    deal_score: DealScoreBreakdown
    recommendation: Recommendation
    charts: VisualizationData
