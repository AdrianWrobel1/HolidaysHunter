"""Integration tests for Offer Analyzer pipeline."""

import pytest
from app.offer_analyzer.service import analyze_offer_url
from app.offer_analyzer.parser import detect_provider_from_url
from app.models.enums import Provider


def test_detect_provider_from_urls():
    assert detect_provider_from_url("https://www.itaka.pl/wczasy/egipt/hotel,123.html") == Provider.ITAKA
    assert detect_provider_from_url("https://www.tui.pl/wypoczynek/hiszpania/hotel") == Provider.TUI
    assert detect_provider_from_url("https://r.pl/szukaj") == Provider.RAINBOW
    assert detect_provider_from_url("https://www.wakacje.pl/oferty/egipt") == Provider.WAKACJE_PL


@pytest.mark.asyncio
async def test_full_offer_analyzer_pipeline_execution():
    test_url = "https://www.itaka.pl/wczasy/hiszpania/teneryfa/hotel-playa-sur,987654.html"

    report = await analyze_offer_url(test_url)

    assert report.target_type == "offer"
    assert report.target_offer.hotel_name is not None
    assert report.target_offer.provider.lower() == "itaka"

    # Verify all analyses exist
    assert report.statistics.target_price > 0
    assert report.market_position.cheaper_than_pct >= 0
    assert report.price_efficiency.efficiency_score >= 0
    assert report.offer_quality.quality_score >= 0
    assert 0 <= report.deal_score.total_score <= 100
    assert report.recommendation.verdict_badge != ""
    assert len(report.charts.histogram_bins) > 0
    assert report.charts.box_plot.min_val <= report.charts.box_plot.max_val
