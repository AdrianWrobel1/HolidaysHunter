"""Unit tests for scoring_service — Travel Score calculation and profile matching."""

from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from app.models.enums import MealType
from app.services.scoring_service import (
    _score_hotel_quality,
    _score_meal_quality,
    _score_price_trend,
    _score_price_value,
    calculate_travel_score,
    offer_matches_profile,
)


def _mock_offer(**overrides):
    offer = MagicMock()
    offer.price_per_person = overrides.get("price_per_person", Decimal("2000"))
    offer.price_total = overrides.get("price_total", Decimal("4000"))
    offer.duration_nights = overrides.get("duration_nights", 7)
    offer.hotel_stars = overrides.get("hotel_stars", 4.0)
    offer.hotel_rating = overrides.get("hotel_rating", 8.5)
    offer.meal_type = overrides.get("meal_type", MealType.ALL_INCLUSIVE)
    offer.price_history = overrides.get("price_history", [])
    offer.country = overrides.get("country", "Grecja")
    offer.region = overrides.get("region", "Kreta")
    offer.departure_city = overrides.get("departure_city", "Warszawa")
    offer.departure_date = overrides.get("departure_date", date(2026, 8, 15))
    offer.adults = overrides.get("adults", 2)
    offer.children = overrides.get("children", 0)
    offer.provider = overrides.get("provider", "itaka")
    offer.travel_score = overrides.get("travel_score", None)
    offer.is_available = overrides.get("is_available", True)
    return offer


def _mock_profile(**overrides):
    profile = MagicMock()
    profile.is_active = overrides.get("is_active", True)
    profile.countries = overrides.get("countries", None)
    profile.regions = overrides.get("regions", None)
    profile.departure_cities = overrides.get("departure_cities", None)
    profile.date_from = overrides.get("date_from", None)
    profile.date_to = overrides.get("date_to", None)
    profile.duration_min = overrides.get("duration_min", None)
    profile.duration_max = overrides.get("duration_max", None)
    profile.budget_min = overrides.get("budget_min", None)
    profile.budget_max = overrides.get("budget_max", None)
    profile.adults = overrides.get("adults", None)
    profile.children = overrides.get("children", None)
    profile.hotel_stars_min = overrides.get("hotel_stars_min", None)
    profile.meal_types = overrides.get("meal_types", None)
    profile.providers = overrides.get("providers", None)
    profile.transport_types = overrides.get("transport_types", None)
    return profile


def _mock_price_history(price: Decimal, recorded_at: datetime):
    ph = MagicMock()
    ph.price_per_person = price
    ph.recorded_at = recorded_at
    return ph


class TestScorePriceValue:
    def test_excellent_deal(self):
        offer = _mock_offer(price_per_person=Decimal("700"), duration_nights=7)
        assert _score_price_value(offer) == 25.0

    def test_good_deal(self):
        offer = _mock_offer(price_per_person=Decimal("1400"), duration_nights=7)
        assert _score_price_value(offer) == 20.0

    def test_average(self):
        offer = _mock_offer(price_per_person=Decimal("2100"), duration_nights=7)
        assert _score_price_value(offer) == 15.0

    def test_expensive(self):
        offer = _mock_offer(price_per_person=Decimal("5000"), duration_nights=7)
        assert _score_price_value(offer) == 5.0

    def test_zero_duration(self):
        offer = _mock_offer(price_per_person=Decimal("2000"), duration_nights=0)
        assert _score_price_value(offer) == 5.0


class TestScorePriceTrend:
    def test_no_history(self):
        offer = _mock_offer(price_history=[])
        assert _score_price_trend(offer) == 0.0

    def test_price_drop_10pct(self):
        offer = _mock_offer(
            price_history=[
                _mock_price_history(Decimal("1000"), datetime(2026, 7, 1, tzinfo=timezone.utc)),
                _mock_price_history(Decimal("900"), datetime(2026, 7, 5, tzinfo=timezone.utc)),
            ]
        )
        score = _score_price_trend(offer)
        assert 5.0 < score < 10.0

    def test_price_increase(self):
        offer = _mock_offer(
            price_history=[
                _mock_price_history(Decimal("1000"), datetime(2026, 7, 1, tzinfo=timezone.utc)),
                _mock_price_history(Decimal("1200"), datetime(2026, 7, 5, tzinfo=timezone.utc)),
            ]
        )
        assert _score_price_trend(offer) == 0.0

    def test_large_drop_capped_at_20(self):
        offer = _mock_offer(
            price_history=[
                _mock_price_history(Decimal("1000"), datetime(2026, 7, 1, tzinfo=timezone.utc)),
                _mock_price_history(Decimal("400"), datetime(2026, 7, 5, tzinfo=timezone.utc)),
            ]
        )
        assert _score_price_trend(offer) == 20.0


class TestScoreHotelQuality:
    def test_five_stars_high_rating(self):
        offer = _mock_offer(hotel_stars=5.0, hotel_rating=9.5)
        assert _score_hotel_quality(offer) == 25.0

    def test_no_data(self):
        offer = _mock_offer(hotel_stars=None, hotel_rating=None)
        assert _score_hotel_quality(offer) == 0.0


class TestScoreMealQuality:
    def test_all_inclusive(self):
        offer = _mock_offer(meal_type=MealType.ALL_INCLUSIVE)
        assert _score_meal_quality(offer) == 15.0

    def test_self_catering(self):
        offer = _mock_offer(meal_type=MealType.SELF_CATERING)
        assert _score_meal_quality(offer) == 0.0


class TestCalculateTravelScore:
    def test_score_in_range(self):
        offer = _mock_offer()
        score = calculate_travel_score(offer, [])
        assert 0 <= score <= 100

    def test_profile_match_boosts_score(self):
        offer = _mock_offer()
        profile = _mock_profile(countries=["Grecja"])
        score_without = calculate_travel_score(offer, [])
        score_with = calculate_travel_score(offer, [profile])
        assert score_with > score_without


class TestOfferMatchesProfile:
    def test_empty_profile_matches_everything(self):
        offer = _mock_offer()
        profile = _mock_profile()
        assert offer_matches_profile(offer, profile) is True

    def test_country_match(self):
        offer = _mock_offer(country="Grecja")
        profile = _mock_profile(countries=["Grecja", "Turcja"])
        assert offer_matches_profile(offer, profile) is True

    def test_country_mismatch(self):
        offer = _mock_offer(country="Egipt")
        profile = _mock_profile(countries=["Grecja", "Turcja"])
        assert offer_matches_profile(offer, profile) is False

    def test_budget_within_range(self):
        offer = _mock_offer(price_per_person=Decimal("2500"))
        profile = _mock_profile(budget_min=Decimal("2000"), budget_max=Decimal("3000"))
        assert offer_matches_profile(offer, profile) is True

    def test_budget_exceeds_max(self):
        offer = _mock_offer(price_per_person=Decimal("3500"))
        profile = _mock_profile(budget_max=Decimal("3000"))
        assert offer_matches_profile(offer, profile) is False

    def test_date_range(self):
        offer = _mock_offer(departure_date=date(2026, 8, 15))
        profile = _mock_profile(date_from=date(2026, 8, 1), date_to=date(2026, 8, 31))
        assert offer_matches_profile(offer, profile) is True

    def test_date_too_early(self):
        offer = _mock_offer(departure_date=date(2026, 7, 15))
        profile = _mock_profile(date_from=date(2026, 8, 1))
        assert offer_matches_profile(offer, profile) is False

    def test_duration_range(self):
        offer = _mock_offer(duration_nights=7)
        profile = _mock_profile(duration_min=5, duration_max=10)
        assert offer_matches_profile(offer, profile) is True

    def test_duration_too_short(self):
        offer = _mock_offer(duration_nights=3)
        profile = _mock_profile(duration_min=5)
        assert offer_matches_profile(offer, profile) is False

    def test_hotel_stars_minimum(self):
        offer = _mock_offer(hotel_stars=3.0)
        profile = _mock_profile(hotel_stars_min=4.0)
        assert offer_matches_profile(offer, profile) is False

    def test_inactive_profile_never_matches(self):
        offer = _mock_offer()
        profile = _mock_profile(is_active=False)
        assert offer_matches_profile(offer, profile) is False

    def test_meal_type_match(self):
        offer = _mock_offer(meal_type=MealType.ALL_INCLUSIVE)
        profile = _mock_profile(meal_types=["all_inclusive", "full_board"])
        assert offer_matches_profile(offer, profile) is True

    def test_meal_type_mismatch(self):
        offer = _mock_offer(meal_type=MealType.SELF_CATERING)
        profile = _mock_profile(meal_types=["all_inclusive"])
        assert offer_matches_profile(offer, profile) is False

    def test_provider_match(self):
        offer = _mock_offer(provider="itaka")
        profile = _mock_profile(providers=["itaka", "tui"])
        assert offer_matches_profile(offer, profile) is True

    def test_multi_criteria_all_must_match(self):
        offer = _mock_offer(
            country="Grecja",
            price_per_person=Decimal("2500"),
            duration_nights=7,
            hotel_stars=4.0,
        )
        profile = _mock_profile(
            countries=["Grecja"],
            budget_max=Decimal("3000"),
            duration_min=5,
            hotel_stars_min=3.0,
        )
        assert offer_matches_profile(offer, profile) is True
