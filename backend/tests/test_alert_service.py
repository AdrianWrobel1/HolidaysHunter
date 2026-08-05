"""Unit tests for alert_service — alert event generation logic."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models.enums import AlertType
from app.services.alert_service import (
    _check_lowest_price,
    _check_price_drop,
)


def _mock_offer(**overrides):
    offer = MagicMock()
    offer.id = overrides.get("id", "test-offer-id")
    offer.hotel_name = overrides.get("hotel_name", "Hotel Sun")
    offer.country = overrides.get("country", "Grecja")
    offer.price_per_person = overrides.get("price_per_person", Decimal("2000"))
    offer.price_history = overrides.get("price_history", [])
    offer.travel_score = overrides.get("travel_score", None)
    offer.provider = overrides.get("provider", "itaka")
    return offer


def _mock_price_history(price: Decimal, recorded_at: datetime):
    ph = MagicMock()
    ph.price_per_person = price
    ph.recorded_at = recorded_at
    return ph


class TestCheckPriceDrop:
    def test_no_history(self):
        offer = _mock_offer(price_history=[])
        assert _check_price_drop(offer, []) is None

    def test_single_entry(self):
        offer = _mock_offer(
            price_history=[
                _mock_price_history(Decimal("1000"), datetime(2026, 7, 1, tzinfo=timezone.utc)),
            ]
        )
        assert _check_price_drop(offer, []) is None

    def test_significant_drop_generates_alert(self):
        offer = _mock_offer(
            price_history=[
                _mock_price_history(Decimal("2000"), datetime(2026, 7, 1, tzinfo=timezone.utc)),
                _mock_price_history(Decimal("1800"), datetime(2026, 7, 5, tzinfo=timezone.utc)),
            ]
        )
        event = _check_price_drop(offer, [])
        assert event is not None
        assert event.alert_type == AlertType.PRICE_DROP

    def test_small_drop_no_alert(self):
        offer = _mock_offer(
            price_history=[
                _mock_price_history(Decimal("2000"), datetime(2026, 7, 1, tzinfo=timezone.utc)),
                _mock_price_history(Decimal("1950"), datetime(2026, 7, 5, tzinfo=timezone.utc)),
            ]
        )
        assert _check_price_drop(offer, []) is None

    def test_price_increase_no_alert(self):
        offer = _mock_offer(
            price_history=[
                _mock_price_history(Decimal("2000"), datetime(2026, 7, 1, tzinfo=timezone.utc)),
                _mock_price_history(Decimal("2200"), datetime(2026, 7, 5, tzinfo=timezone.utc)),
            ]
        )
        assert _check_price_drop(offer, []) is None


class TestCheckLowestPrice:
    def test_fewer_than_3_entries(self):
        offer = _mock_offer(
            price_history=[
                _mock_price_history(Decimal("2000"), datetime(2026, 7, 1, tzinfo=timezone.utc)),
                _mock_price_history(Decimal("1800"), datetime(2026, 7, 5, tzinfo=timezone.utc)),
            ]
        )
        assert _check_lowest_price(offer) is None

    def test_new_lowest_generates_alert(self):
        offer = _mock_offer(
            price_history=[
                _mock_price_history(Decimal("2000"), datetime(2026, 7, 1, tzinfo=timezone.utc)),
                _mock_price_history(Decimal("1900"), datetime(2026, 7, 15, tzinfo=timezone.utc)),
                _mock_price_history(Decimal("1700"), datetime(2026, 8, 1, tzinfo=timezone.utc)),
            ]
        )
        event = _check_lowest_price(offer)
        assert event is not None
        assert event.alert_type == AlertType.LOWEST_PRICE

    def test_not_lowest_no_alert(self):
        offer = _mock_offer(
            price_history=[
                _mock_price_history(Decimal("2000"), datetime(2026, 7, 1, tzinfo=timezone.utc)),
                _mock_price_history(Decimal("1500"), datetime(2026, 7, 15, tzinfo=timezone.utc)),
                _mock_price_history(Decimal("1700"), datetime(2026, 8, 1, tzinfo=timezone.utc)),
            ]
        )
        assert _check_lowest_price(offer) is None
