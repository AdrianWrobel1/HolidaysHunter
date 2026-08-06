from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class PriceHistoryResponse(BaseModel):
    """Single price history entry."""

    id: UUID
    price_total: Decimal
    price_per_person: Decimal
    recorded_at: datetime

    model_config = {"from_attributes": True}


class OfferResponse(BaseModel):
    """API response schema for a single offer in list view."""

    id: UUID
    external_id: str
    provider: str

    title: str
    country: str
    region: str | None
    city: str | None

    hotel_name: str
    hotel_stars: float | None
    hotel_rating: float | None

    departure_date: date
    return_date: date
    duration_nights: int
    departure_city: str

    adults: int
    children: int

    meal_type: str
    transport_type: str

    price_total: Decimal
    price_per_person: Decimal
    currency: str

    offer_url: str | None = None
    image_url: str | None

    travel_score: int | None
    is_available: bool

    model_config = {"from_attributes": True}


class OfferDetailResponse(OfferResponse):
    """Extended offer response with price history and computed fields."""

    first_seen_at: datetime
    last_seen_at: datetime
    price_history: list[PriceHistoryResponse]
    price_change_pct: float | None
    days_available: int


class OffersListResponse(BaseModel):
    """Paginated response for the offers list."""

    offers: list[OfferResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FilterOptionsResponse(BaseModel):
    """Available filter values for the Explorer UI."""

    countries: list[str]
    regions: list[str]
    country_regions: dict[str, list[str]] = {}
    departure_cities: list[str]
    providers: list[str]
    meal_types: list[str]
    transport_types: list[str]


# --- Travel Profiles ---


class TravelProfileCreate(BaseModel):
    """Schema for creating a new travel profile."""

    name: str
    countries: list[str] | None = None
    regions: list[str] | None = None
    departure_cities: list[str] | None = None
    date_from: date | None = None
    date_to: date | None = None
    duration_min: int | None = None
    duration_max: int | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    adults: int | None = None
    children: int | None = None
    hotel_stars_min: float | None = None
    meal_types: list[str] | None = None
    providers: list[str] | None = None
    transport_types: list[str] | None = None
    notification_policy: str | None = "HIGH_AND_MUST_SEE"


class TravelProfileUpdate(BaseModel):
    """Schema for updating a travel profile. All fields optional."""

    name: str | None = None
    countries: list[str] | None = None
    regions: list[str] | None = None
    departure_cities: list[str] | None = None
    date_from: date | None = None
    date_to: date | None = None
    duration_min: int | None = None
    duration_max: int | None = None
    budget_min: Decimal | None = None
    budget_max: Decimal | None = None
    adults: int | None = None
    children: int | None = None
    hotel_stars_min: float | None = None
    meal_types: list[str] | None = None
    providers: list[str] | None = None
    transport_types: list[str] | None = None
    notification_policy: str | None = None
    is_active: bool | None = None


class TravelProfileResponse(BaseModel):
    """API response schema for a travel profile."""

    id: UUID
    name: str
    countries: list[str] | None
    regions: list[str] | None
    departure_cities: list[str] | None
    date_from: date | None
    date_to: date | None
    duration_min: int | None
    duration_max: int | None
    budget_min: Decimal | None
    budget_max: Decimal | None
    adults: int | None
    children: int | None
    hotel_stars_min: float | None
    meal_types: list[str] | None
    providers: list[str] | None
    transport_types: list[str] | None = None
    notification_policy: str = "HIGH_AND_MUST_SEE"
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Alerts ---


class AlertEventResponse(BaseModel):
    """API response schema for an alert event."""

    id: UUID
    offer_id: UUID
    profile_id: UUID | None
    alert_type: str
    message: str
    priority_score: float | None = None
    priority_level: str | None = None
    reasons_json: dict | list | None = None
    metadata_json: dict | None
    is_read: bool
    triggered_at: datetime

    model_config = {"from_attributes": True}


class AlertsListResponse(BaseModel):
    """Paginated response for alert events."""

    alerts: list[AlertEventResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- Seasonal Analytics V2 ---


class SeasonalExecutiveSummary(BaseModel):
    cheapest_month: dict | None = None
    most_expensive_month: dict | None = None
    potential_savings: dict | None = None
    best_value_month: dict | None = None
    biggest_price_drop: dict | None = None


class MonthlyHeatmapItem(BaseModel):
    month: int
    month_name: str
    season: str
    avg_price: float
    median_price: float
    min_price: float
    max_price: float
    p10: float
    p25: float
    p75: float
    p90: float
    offer_count: int
    avg_deal_score: float
    avg_value_score: float
    price_level: str  # low | medium | high


class PriceTrendPoint(BaseModel):
    period: str
    month: int
    month_name: str
    avg: float
    median: float
    min: float
    max: float
    p10: float
    p25: float
    p75: float
    p90: float
    count: int


class DistributionBucket(BaseModel):
    range_min: float
    range_max: float
    label: str
    count: int


class BoxPlotData(BaseModel):
    min: float
    p25: float
    median: float
    p75: float
    max: float
    mean: float


class PriceDistribution(BaseModel):
    buckets: list[DistributionBucket]
    box_plot: BoxPlotData
    market_median: float
    best_deals_threshold: float


class SeasonalityScore(BaseModel):
    score: int
    level: str
    description: str


class LeadTimeBreakdown(BaseModel):
    window: str
    avg_price: float
    count: int


class BestTimeToBuy(BaseModel):
    recommendation: str  # BUY_NOW | WAIT | TOO_EARLY | TOO_LATE
    title: str
    explanation: str
    estimated_savings_pct: float
    lead_time_breakdown: list[LeadTimeBreakdown]


class RegionalStat(BaseModel):
    country: str
    region: str | None
    avg_price: float
    median_price: float
    cheapest_month_name: str
    most_expensive_month_name: str
    seasonality_score: int
    avg_deal_score: float
    avg_value_score: float
    offer_count: int


class ProviderStat(BaseModel):
    provider: str
    avg_price: float
    median_price: float
    avg_deal_score: float
    avg_value_score: float
    cheapest_month_name: str
    offer_count: int


class MonthlyTransportItem(BaseModel):
    month: int
    month_name: str
    flight_avg: float
    self_avg: float


class TransportAnalysis(BaseModel):
    flight_avg_price: float | None
    self_transport_avg_price: float | None
    flight_premium: float | None
    transport_split: dict[str, int]
    monthly_comparison: list[MonthlyTransportItem]


class PriceForecast(BaseModel):
    next_month_name: str
    expected_price: float
    confidence_pct: int
    trend_direction: str  # ↓↓ | ↓ | → | ↑ | ↑↑
    summary: str


class EmptyStateDiagnostics(BaseModel):
    has_data: bool
    reason: str | None = None
    conflicting_filters: list[str] = []
    suggested_countries: list[str] = []


class SeasonalAnalyticsResponse(BaseModel):
    total_offers_analyzed: int
    active_filters: dict
    executive_summary: SeasonalExecutiveSummary
    monthly_heatmap: list[MonthlyHeatmapItem]
    price_trends: list[PriceTrendPoint]
    price_distribution: PriceDistribution
    seasonality_score: SeasonalityScore
    best_time_to_buy: BestTimeToBuy
    regional_comparison: list[RegionalStat]
    provider_comparison: list[ProviderStat]
    transport_analysis: TransportAnalysis
    price_forecast: PriceForecast
    smart_insights: list[str]
    diagnostics: EmptyStateDiagnostics


