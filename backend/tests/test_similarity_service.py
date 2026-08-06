"""Tests for SimilarityService."""

from datetime import date
from decimal import Decimal
from app.services.similarity import SimilarityService
from app.providers.schemas import NormalizedOffer
from app.models.enums import MealType, Provider, TransportType


def test_similarity_service_identical_and_different_offers():
    offer_a = NormalizedOffer(
        external_id="ext-1",
        provider=Provider.ITAKA,
        title="Hotel Sunrise Grand",
        country="Egipt",
        region="Hurghada",
        city="Hurghada",
        hotel_name="Hotel Sunrise Grand",
        hotel_stars=5.0,
        hotel_rating=9.1,
        departure_date=date(2026, 9, 15),
        return_date=date(2026, 9, 22),
        duration_nights=7,
        departure_city="Warszawa",
        adults=2,
        children=0,
        meal_type=MealType.ALL_INCLUSIVE,
        transport_type=TransportType.FLIGHT,
        price_total=Decimal("5000.00"),
        price_per_person=Decimal("2500.00"),
    )

    offer_b = NormalizedOffer(
        external_id="ext-2",
        provider=Provider.TUI,
        title="Hotel Sunrise Grand Resort",
        country="Egipt",
        region="Hurghada",
        city="Hurghada",
        hotel_name="Hotel Sunrise Grand",
        hotel_stars=5.0,
        hotel_rating=9.0,
        departure_date=date(2026, 9, 16),
        return_date=date(2026, 9, 23),
        duration_nights=7,
        departure_city="Warszawa",
        adults=2,
        children=0,
        meal_type=MealType.ALL_INCLUSIVE,
        transport_type=TransportType.FLIGHT,
        price_total=Decimal("4900.00"),
        price_per_person=Decimal("2450.00"),
    )

    service = SimilarityService()
    match = service.calculate_similarity(offer_a, offer_b)

    assert match.similarity_score >= 85.0
    assert any("Ten sam hotel" in exp for exp in match.explanations)
    assert any("Ten sam kraj" in exp for exp in match.explanations)
    assert any("Ten sam region" in exp for exp in match.explanations)


def test_similarity_ranking():
    target = NormalizedOffer(
        external_id="target",
        provider=Provider.ITAKA,
        title="Hotel Target",
        country="Grecja",
        region="Kreta",
        city="Chania",
        hotel_name="Hotel Target",
        hotel_stars=4.0,
        departure_date=date(2026, 8, 1),
        return_date=date(2026, 8, 8),
        duration_nights=7,
        departure_city="Poznań",
        adults=2,
        children=0,
        meal_type=MealType.HALF_BOARD,
        transport_type=TransportType.FLIGHT,
        price_total=Decimal("3000.00"),
        price_per_person=Decimal("1500.00"),
    )

    close_match = NormalizedOffer(
        external_id="close",
        provider=Provider.RAINBOW,
        title="Hotel Target Resort",
        country="Grecja",
        region="Kreta",
        city="Chania",
        hotel_name="Hotel Target",
        hotel_stars=4.0,
        departure_date=date(2026, 8, 1),
        return_date=date(2026, 8, 8),
        duration_nights=7,
        departure_city="Poznań",
        adults=2,
        children=0,
        meal_type=MealType.HALF_BOARD,
        transport_type=TransportType.FLIGHT,
        price_total=Decimal("2900.00"),
        price_per_person=Decimal("1450.00"),
    )

    far_match = NormalizedOffer(
        external_id="far",
        provider=Provider.WAKACJE_PL,
        title="Hotel Different",
        country="Hiszpania",
        region="Majorca",
        city="Palma",
        hotel_name="Hotel Different",
        hotel_stars=3.0,
        departure_date=date(2026, 11, 1),
        return_date=date(2026, 11, 8),
        duration_nights=7,
        departure_city="Gdańsk",
        adults=2,
        children=0,
        meal_type=MealType.BED_AND_BREAKFAST,
        transport_type=TransportType.FLIGHT,
        price_total=Decimal("8000.00"),
        price_per_person=Decimal("4000.00"),
    )

    service = SimilarityService()
    ranked = service.rank_similar_offers(target, [far_match, close_match])

    assert len(ranked) == 2
    assert ranked[0].offer_id == "close"
    assert ranked[0].similarity_score > ranked[1].similarity_score
