"""Integration tests for offers API endpoints.

Uses FastAPI TestClient with mocked service layer to test endpoint
behavior without requiring a live database.
"""

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def _mock_offer(**overrides):
    """Create a mock Offer ORM object with all required fields."""
    defaults = {
        "id": uuid.uuid4(),
        "external_id": "EXT-001",
        "provider": "itaka",
        "title": "Grecja Kreta Hotel Sun",
        "country": "Grecja",
        "region": "Kreta",
        "city": "Heraklion",
        "hotel_name": "Hotel Sun",
        "hotel_stars": 4.0,
        "hotel_rating": 8.5,
        "departure_date": date(2026, 8, 15),
        "return_date": date(2026, 8, 22),
        "duration_nights": 7,
        "departure_city": "Warszawa",
        "adults": 2,
        "children": 0,
        "meal_type": "all_inclusive",
        "transport_type": "flight",
        "price_total": Decimal("4500.00"),
        "price_per_person": Decimal("2250.00"),
        "currency": "PLN",
        "offer_url": "https://itaka.pl/offer/123",
        "image_url": "https://itaka.pl/img/123.jpg",
        "travel_score": None,
        "is_available": True,
        "first_seen_at": datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc),
        "last_seen_at": datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc),
        "price_history": [],
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


class TestListOffersEndpoint:
    @patch("app.api.offers.list_offers", new_callable=AsyncMock)
    @patch("app.api.offers.get_session")
    def test_returns_empty_list(self, mock_session, mock_list, client):
        mock_list.return_value = ([], 0)
        mock_session.return_value = AsyncMock()

        response = client.get("/api/offers")
        assert response.status_code == 200
        data = response.json()
        assert data["offers"] == []
        assert data["total"] == 0
        assert data["total_pages"] == 0

    @patch("app.api.offers.list_offers", new_callable=AsyncMock)
    @patch("app.api.offers.get_session")
    def test_returns_offers(self, mock_session, mock_list, client):
        offer = _mock_offer()
        mock_list.return_value = ([offer], 1)
        mock_session.return_value = AsyncMock()

        response = client.get("/api/offers")
        assert response.status_code == 200
        data = response.json()
        assert len(data["offers"]) == 1
        assert data["total"] == 1
        assert data["total_pages"] == 1

    def test_invalid_sort_by_returns_400(self, client):
        response = client.get("/api/offers?sort_by=invalid_field")
        assert response.status_code == 400

    def test_invalid_sort_order_returns_422(self, client):
        response = client.get("/api/offers?sort_order=sideways")
        assert response.status_code == 422

    def test_search_too_short_returns_422(self, client):
        response = client.get("/api/offers?search=a")
        assert response.status_code == 422

    def test_negative_price_returns_422(self, client):
        response = client.get("/api/offers?price_min=-100")
        assert response.status_code == 422

    def test_hotel_stars_out_of_range_returns_422(self, client):
        response = client.get("/api/offers?hotel_stars_min=6")
        assert response.status_code == 422


class TestGetOfferEndpoint:
    @patch("app.api.offers.get_offer_detail", new_callable=AsyncMock)
    @patch("app.api.offers.get_session")
    def test_returns_offer_detail(self, mock_session, mock_detail, client):
        offer = _mock_offer()
        mock_detail.return_value = offer
        mock_session.return_value = AsyncMock()

        response = client.get(f"/api/offers/{offer.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["hotel_name"] == "Hotel Sun"
        assert data["days_available"] >= 0

    @patch("app.api.offers.get_offer_detail", new_callable=AsyncMock)
    @patch("app.api.offers.get_session")
    def test_nonexistent_offer_returns_404(self, mock_session, mock_detail, client):
        mock_detail.return_value = None
        mock_session.return_value = AsyncMock()

        fake_id = uuid.uuid4()
        response = client.get(f"/api/offers/{fake_id}")
        assert response.status_code == 404

    def test_invalid_uuid_returns_422(self, client):
        response = client.get("/api/offers/not-a-uuid")
        assert response.status_code == 422


class TestPriceHistoryEndpoint:
    @patch("app.api.offers.get_price_history", new_callable=AsyncMock)
    @patch("app.api.offers.get_session")
    def test_returns_history(self, mock_session, mock_history, client):
        ph = MagicMock()
        ph.id = uuid.uuid4()
        ph.price_total = Decimal("4500.00")
        ph.price_per_person = Decimal("2250.00")
        ph.recorded_at = datetime(2026, 7, 1, 12, 0, 0, tzinfo=timezone.utc)

        mock_history.return_value = [ph]
        mock_session.return_value = AsyncMock()

        fake_id = uuid.uuid4()
        response = client.get(f"/api/offers/{fake_id}/price-history")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    @patch("app.api.offers.get_price_history", new_callable=AsyncMock)
    @patch("app.api.offers.get_session")
    def test_nonexistent_offer_returns_404(self, mock_session, mock_history, client):
        mock_history.return_value = None
        mock_session.return_value = AsyncMock()

        fake_id = uuid.uuid4()
        response = client.get(f"/api/offers/{fake_id}/price-history")
        assert response.status_code == 404


class TestFiltersEndpoint:
    @patch("app.api.offers.get_filter_options", new_callable=AsyncMock)
    @patch("app.api.offers.get_session")
    def test_returns_filter_options(self, mock_session, mock_filters, client):
        mock_filters.return_value = {
            "countries": ["Grecja", "Turcja"],
            "regions": ["Kreta", "Riwiera"],
            "departure_cities": ["Warszawa", "Kraków"],
            "providers": ["itaka", "tui"],
            "meal_types": ["all_inclusive"],
            "transport_types": ["flight"],
        }
        mock_session.return_value = AsyncMock()

        response = client.get("/api/offers/filters")
        assert response.status_code == 200
        data = response.json()
        assert "Grecja" in data["countries"]
        assert len(data["providers"]) == 2
