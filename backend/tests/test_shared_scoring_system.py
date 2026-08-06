"""Tests for Shared Scoring & Ranking System (app.scoring)."""

from datetime import date, timedelta
from app.models.enums import Provider, MealType, TransportType
from app.providers.schemas import NormalizedOffer
from app.scoring import (
    DealScoreEngine,
    ValueEngine,
    ConfidenceEngine,
    RankingEngine,
    RankingProfile,
)
from app.services.similarity import SimilarityService


def _create_sample_offer(
    ext_id: str = "test-1",
    stars: float = 4.0,
    rating: float = 8.5,
    price_pp: float = 3000.0,
    transport: TransportType = TransportType.FLIGHT,
    meal: MealType = MealType.ALL_INCLUSIVE,
) -> NormalizedOffer:
    today = date.today()
    return NormalizedOffer(
        external_id=ext_id,
        provider=Provider.ITAKA,
        title=f"Test Offer {ext_id}",
        country="Hiszpania",
        region="Teneryfa",
        hotel_name=f"Hotel {ext_id}",
        hotel_stars=stars,
        hotel_rating=rating,
        departure_date=today + timedelta(days=10),
        return_date=today + timedelta(days=17),
        duration_nights=7,
        departure_city="Warszawa",
        adults=2,
        children=0,
        meal_type=meal,
        transport_type=transport,
        price_total=price_pp * 2,
        price_per_person=price_pp,
        currency="PLN",
    )


def test_value_engine_calculation():
    engine = ValueEngine()
    offer = _create_sample_offer(stars=5.0, rating=9.2, price_pp=2500.0)

    val_res = engine.calculate(offer)
    assert 0 <= val_res.total_score <= 100
    assert len(val_res.components) == 5
    assert len(val_res.explanations) > 0

    # Ensure each component has impact and explanation
    for comp in val_res.components:
        assert comp.name is not None
        assert 0 <= comp.score <= 100
        assert comp.explanation is not None


def test_deal_score_engine_and_confidence():
    engine = DealScoreEngine()
    offer = _create_sample_offer(stars=4.0, rating=8.0, price_pp=2800.0)

    ctx = {
        "candidates_count": 25,
        "price_history": [1, 2, 3],
        "market_position": {"cheaper_than_pct": 82.0},
    }

    deal_res = engine.calculate(offer, context=ctx, diagnostic=True)
    assert 0 <= deal_res.total_score <= 100
    assert deal_res.confidence.score > 0
    assert deal_res.confidence.level in ("HIGH", "MEDIUM", "LOW")
    assert len(deal_res.components) >= 5
    assert len(deal_res.explanations) > 0
    assert "components" in deal_res.diagnostic_details


def test_ranking_engine_profiles():
    ranking = RankingEngine()

    offer_cheap = _create_sample_offer(ext_id="cheap", stars=3.0, rating=7.0, price_pp=1500.0)
    offer_luxury = _create_sample_offer(ext_id="luxury", stars=5.0, rating=9.5, price_pp=6000.0)
    offer_balanced = _create_sample_offer(ext_id="balanced", stars=4.0, rating=8.5, price_pp=2800.0)

    offers = [offer_cheap, offer_luxury, offer_balanced]

    # Test BUDGET profile: cheap offer should rank highest
    budget_ranks = ranking.rank_offers(offers, profile=RankingProfile.BUDGET)
    assert budget_ranks[0].offer_object.external_id == "cheap"

    # Test LUXURY profile: luxury offer should rank highest
    luxury_ranks = ranking.rank_offers(offers, profile=RankingProfile.LUXURY)
    assert luxury_ranks[0].offer_object.external_id == "luxury"


def test_similarity_transport_mismatch_penalty():
    service = SimilarityService()

    target_flight = _create_sample_offer(ext_id="flight", transport=TransportType.FLIGHT)
    cand_flight = _create_sample_offer(ext_id="flight2", transport=TransportType.FLIGHT)
    cand_self = _create_sample_offer(ext_id="self", transport=TransportType.SELF_TRANSPORT)

    res_same = service.calculate_similarity(target_flight, cand_flight)
    res_diff = service.calculate_similarity(target_flight, cand_self)

    # Offer with transport mismatch should score significantly lower due to penalty
    assert res_same.similarity_score > res_diff.similarity_score
    assert any("Inny typ transportu" in exp or "Różny typ transportu" in exp for exp in res_diff.explanations)
