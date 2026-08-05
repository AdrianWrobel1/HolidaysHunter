"""Unit tests for offer_service — compute functions and sort column mapping."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.services.offer_service import (
    _get_sort_column,
    compute_days_available,
    compute_price_change_pct,
)
from app.models.offer import Offer


def _make_offer(**overrides) -> Offer:
    """Create a minimal Offer instance for testing."""
    offer = MagicMock(spec=Offer)
    offer.first_seen_at = overrides.get(
        "first_seen_at", datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
    )
    offer.price_history = overrides.get("price_history", [])
    return offer


def _make_price_history(price_per_person: Decimal, recorded_at: datetime) -> MagicMock:
    """Create a minimal PriceHistory mock."""
    ph = MagicMock()
    ph.price_per_person = price_per_person
    ph.recorded_at = recorded_at
    return ph


class TestComputePriceChangePct:
    def test_no_history_returns_none(self):
        offer = _make_offer(price_history=[])
        assert compute_price_change_pct(offer) is None

    def test_single_entry_returns_none(self):
        offer = _make_offer(
            price_history=[
                _make_price_history(
                    Decimal("1000"), datetime(2026, 7, 1, tzinfo=timezone.utc)
                ),
            ]
        )
        assert compute_price_change_pct(offer) is None

    def test_price_drop(self):
        offer = _make_offer(
            price_history=[
                _make_price_history(
                    Decimal("1000"), datetime(2026, 7, 1, tzinfo=timezone.utc)
                ),
                _make_price_history(
                    Decimal("800"), datetime(2026, 7, 5, tzinfo=timezone.utc)
                ),
            ]
        )
        result = compute_price_change_pct(offer)
        assert result == -20.0

    def test_price_increase(self):
        offer = _make_offer(
            price_history=[
                _make_price_history(
                    Decimal("1000"), datetime(2026, 7, 1, tzinfo=timezone.utc)
                ),
                _make_price_history(
                    Decimal("1150"), datetime(2026, 7, 5, tzinfo=timezone.utc)
                ),
            ]
        )
        result = compute_price_change_pct(offer)
        assert result == 15.0

    def test_zero_first_price_returns_none(self):
        offer = _make_offer(
            price_history=[
                _make_price_history(
                    Decimal("0"), datetime(2026, 7, 1, tzinfo=timezone.utc)
                ),
                _make_price_history(
                    Decimal("500"), datetime(2026, 7, 5, tzinfo=timezone.utc)
                ),
            ]
        )
        assert compute_price_change_pct(offer) is None

    def test_no_change(self):
        offer = _make_offer(
            price_history=[
                _make_price_history(
                    Decimal("2000"), datetime(2026, 7, 1, tzinfo=timezone.utc)
                ),
                _make_price_history(
                    Decimal("2000"), datetime(2026, 7, 5, tzinfo=timezone.utc)
                ),
            ]
        )
        result = compute_price_change_pct(offer)
        assert result == 0.0

    def test_uses_chronological_order(self):
        """Even if history is passed out of order, uses earliest/latest."""
        offer = _make_offer(
            price_history=[
                _make_price_history(
                    Decimal("800"), datetime(2026, 7, 10, tzinfo=timezone.utc)
                ),
                _make_price_history(
                    Decimal("1000"), datetime(2026, 7, 1, tzinfo=timezone.utc)
                ),
            ]
        )
        result = compute_price_change_pct(offer)
        assert result == -20.0


class TestComputeDaysAvailable:
    def test_basic_calculation(self):
        first_seen = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)
        offer = _make_offer(first_seen_at=first_seen)
        days = compute_days_available(offer)
        assert days >= 0

    def test_naive_datetime_treated_as_utc(self):
        first_seen = datetime(2026, 7, 1, 12, 0, 0)
        offer = _make_offer(first_seen_at=first_seen)
        days = compute_days_available(offer)
        assert days >= 0

    def test_never_negative(self):
        future = datetime(2030, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        offer = _make_offer(first_seen_at=future)
        assert compute_days_available(offer) == 0


class TestGetSortColumn:
    def test_valid_columns(self):
        for col_name in [
            "price_per_person",
            "price_total",
            "travel_score",
            "departure_date",
            "hotel_stars",
            "hotel_rating",
            "duration_nights",
        ]:
            column = _get_sort_column(col_name)
            assert column is not None

    def test_unknown_falls_back_to_price(self):
        column = _get_sort_column("nonexistent")
        assert column.key == "price_per_person"
