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

