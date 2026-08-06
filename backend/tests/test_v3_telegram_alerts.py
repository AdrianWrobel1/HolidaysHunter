"""Unit tests for Telegram Alerts V3 — Priority Engine, Cooldown Policy, Watchlist, Timeline, and Formatting."""

from decimal import Decimal
import pytest
from app.models.enums import AlertType, TransportType
from app.models.offer import Offer
from app.models.travel_profile import TravelProfile
from app.services.alert_priority import (
    AlertReasonEnum,
    PriorityLevel,
    calculate_alert_priority,
)


def test_calculate_alert_priority_must_see():
    """Test MUST_SEE priority score calculation for exceptional offer."""
    offer = Offer(
        external_id="test1",
        provider="itaka",
        title="Super Deal",
        country="Egipt",
        hotel_name="Luxury Resort",
        hotel_stars=5.0,
        hotel_rating=9.5,
        departure_date="2026-09-01",
        return_date="2026-09-08",
        duration_nights=7,
        departure_city="Katowice",
        adults=2,
        children=0,
        meal_type="all_inclusive",
        transport_type="flight",
        price_total=Decimal("3000.00"),
        price_per_person=Decimal("1500.00"),
        travel_score=95,
    )
    profile = TravelProfile(name="Egipt AI <3000", is_active=True)

    result = calculate_alert_priority(
        offer=offer,
        alert_type=AlertType.PRICE_DROP,
        profile=profile,
        previous_price=Decimal("2000.00"),  # 25% price drop
        is_lowest_price=True,
    )

    assert result.priority_score >= 85.0
    assert result.priority_level == PriorityLevel.MUST_SEE
    assert AlertReasonEnum.PRICE_DROP in result.reasons
    assert AlertReasonEnum.NEW_LOWEST_PRICE in result.reasons
    assert len(result.value_reasons) > 0
    assert len(result.now_reasons) > 0


def test_calculate_alert_priority_low():
    """Test LOW priority score calculation for routine offer."""
    offer = Offer(
        external_id="test2",
        provider="tui",
        title="Standard Offer",
        country="Chorwacja",
        hotel_name="Basic Apartments",
        hotel_stars=2.0,
        hotel_rating=6.0,
        departure_date="2026-09-01",
        return_date="2026-09-08",
        duration_nights=7,
        departure_city="Kraków",
        adults=2,
        children=0,
        meal_type="self_catering",
        transport_type="self_transport",
        price_total=Decimal("6000.00"),
        price_per_person=Decimal("3000.00"),
        travel_score=40,
    )

    result = calculate_alert_priority(
        offer=offer,
        alert_type=AlertType.NEW_MATCH,
        profile=None,
        previous_price=None,
        is_lowest_price=False,
    )

    assert result.priority_score < 60.0
    assert result.priority_level in (PriorityLevel.NORMAL, PriorityLevel.LOW)
