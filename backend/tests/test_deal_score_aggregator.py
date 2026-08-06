"""Tests for Deal Score components and Aggregator."""

from decimal import Decimal
from app.analysis_framework import AnalysisContext
from app.analysis_framework.deal_score import (
    CompletenessScoreComponent,
    DealScoreAggregator,
    MarketScoreComponent,
    PriceScoreComponent,
    QualityScoreComponent,
    SeasonScoreComponent,
    SimilarityScoreComponent,
)
from app.providers.schemas import NormalizedOffer
from app.models.enums import MealType, Provider, TransportType


def test_deal_score_aggregator_calculation():
    offer = NormalizedOffer(
        external_id="ext-100",
        provider=Provider.ITAKA,
        title="Hotel Paradise Beach",
        country="Hiszpania",
        region="Teneryfa",
        city="Adeje",
        hotel_name="Hotel Paradise Beach",
        hotel_stars=4.0,
        hotel_rating=8.8,
        departure_date="2026-09-10",
        return_date="2026-09-17",
        duration_nights=7,
        departure_city="Katowice",
        adults=2,
        children=0,
        meal_type=MealType.ALL_INCLUSIVE,
        transport_type=TransportType.FLIGHT,
        price_total=Decimal("4000.00"),
        price_per_person=Decimal("2000.00"),
        offer_url="https://www.itaka.pl/wczasy/hiszpania/teneryfa/hotel-paradise-beach,123.html",
        image_url="https://images.itaka.pl/img.jpg",
    )

    context = AnalysisContext(analyzed_object=offer)
    context.artifacts.set("statistics", {"mean_price_per_person": 2500.0})
    context.artifacts.set("market_position", {"cheaper_than_pct": 75.0})

    aggregator = DealScoreAggregator([
        PriceScoreComponent(),
        SimilarityScoreComponent(),
        MarketScoreComponent(),
        QualityScoreComponent(),
        SeasonScoreComponent(),
        CompletenessScoreComponent(),
    ])

    score = aggregator.calculate(context)

    assert 0 <= score.total_score <= 100
    assert "price_score" in score.components
    assert "completeness_score" in score.components
    assert score.summary != ""
