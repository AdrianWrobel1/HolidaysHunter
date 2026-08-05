"""Unit and API integration tests for Offer QA module and Single Offer Debugger."""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.enums import MealType, Provider, TransportType
from app.providers.schemas import NormalizedOffer
from app.services.qa_service import debug_offer_by_id, run_qa_audit, validate_offer


@pytest.fixture
def client():
    return TestClient(app)


def test_validate_offer_valid():
    normalized = NormalizedOffer(
        external_id="TEST-001",
        provider=Provider.TUI,
        title="Test Hotel Palma",
        country="Hiszpania",
        region="Majorka",
        city="Palma de Mallorca",
        hotel_name="Test Hotel Palma",
        hotel_stars=4.0,
        hotel_rating=8.5,
        departure_date=date(2026, 8, 20),
        return_date=date(2026, 8, 27),
        duration_nights=7,
        departure_city="Warszawa",
        adults=2,
        children=0,
        meal_type=MealType.ALL_INCLUSIVE,
        transport_type=TransportType.FLIGHT,
        price_total=Decimal("6000.00"),
        price_per_person=Decimal("3000.00"),
    )

    errors = validate_offer({"raw": "sample"}, normalized)
    assert errors == [], f"Expected no errors, got: {errors}"


def test_validate_offer_invalid_country_and_price():
    # Test with uncanonicalized country and invalid price total < price_per_person
    normalized = NormalizedOffer(
        external_id="TEST-002",
        provider=Provider.ITAKA,
        title="Test Hotel Incorrect",
        country="hiszpania",  # uncanonicalized string
        region="Majorka",
        city="Palma",
        hotel_name="Test Hotel Incorrect",
        hotel_stars=4.0,
        hotel_rating=8.5,
        departure_date=date(2026, 8, 20),
        return_date=date(2026, 8, 27),
        duration_nights=7,
        departure_city="Warszawa",
        adults=2,
        children=0,
        meal_type=MealType.ALL_INCLUSIVE,
        transport_type=TransportType.FLIGHT,
        price_total=Decimal("1000.00"),
        price_per_person=Decimal("3000.00"),
    )

    errors = validate_offer(None, normalized)
    assert any("invalid_country" in e for e in errors)
    assert any("invalid_price" in e for e in errors)


@patch("app.api.qa.get_latest_qa_report")
def test_get_debug_qa_endpoint(mock_get_report, client):
    mock_get_report.return_value = {
        "timestamp": "2026-08-05T23:00:00Z",
        "summary": {
            "total_imported": 10,
            "total_valid": 10,
            "total_invalid": 0,
            "invalid_breakdown": {},
        },
        "filter_tests": [{"filter_name": "country", "status": "PASSED"}],
        "invalid_offers_count": 0,
        "invalid_offers_lineage": [],
    }

    response = client.get("/debug/qa")
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["total_imported"] == 10
    assert data["filter_tests"][0]["filter_name"] == "country"


@patch("app.api.qa.debug_offer_by_id", new_callable=AsyncMock)
def test_get_debug_offer_endpoint(mock_debug, client):
    mock_debug.return_value = {
        "offer_id": "12345",
        "external_id": "TUI-PL-2026-001",
        "provider": "tui",
        "title": "TUI Magic Hotel",
        "is_valid": True,
        "lineage": {
            "1_raw_api": {"sample": "raw"},
            "2_normalized_offer": {"external_id": "TUI-PL-2026-001"},
            "3_db_record": {"id": "12345"},
            "4_filter_results": [{"filter": "country", "status": "PASS"}],
        },
    }

    response = client.get("/debug/offer/TUI-PL-2026-001")
    assert response.status_code == 200
    data = response.json()
    assert data["external_id"] == "TUI-PL-2026-001"
    assert "lineage" in data
    assert data["lineage"]["4_filter_results"][0]["status"] == "PASS"
