"""Integration tests for profiles and alerts API endpoints."""

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


def _mock_profile(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "name": "Wakacje Grecja",
        "countries": ["Grecja"],
        "regions": None,
        "departure_cities": ["Warszawa"],
        "date_from": date(2026, 8, 1),
        "date_to": date(2026, 8, 31),
        "duration_min": 5,
        "duration_max": 10,
        "budget_min": None,
        "budget_max": Decimal("3000"),
        "adults": 2,
        "children": 0,
        "hotel_stars_min": 3.0,
        "meal_types": ["all_inclusive"],
        "providers": None,
        "is_active": True,
        "created_at": datetime(2026, 7, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 7, 1, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


def _mock_alert(**overrides):
    defaults = {
        "id": uuid.uuid4(),
        "offer_id": uuid.uuid4(),
        "profile_id": uuid.uuid4(),
        "alert_type": "new_match",
        "message": "Nowa oferta pasująca do profilu",
        "metadata_json": {"price_per_person": "2250.00"},
        "is_read": False,
        "triggered_at": datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc),
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    return mock


class TestProfilesAPI:
    @patch("app.api.profiles.get_profiles", new_callable=AsyncMock)
    @patch("app.api.profiles.get_session")
    def test_list_profiles(self, mock_session, mock_list, client):
        profile = _mock_profile()
        mock_list.return_value = [profile]
        mock_session.return_value = AsyncMock()

        response = client.get("/api/profiles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Wakacje Grecja"

    @patch("app.api.profiles.create_profile", new_callable=AsyncMock)
    @patch("app.api.profiles.get_session")
    def test_create_profile(self, mock_session, mock_create, client):
        profile = _mock_profile()
        mock_create.return_value = profile
        mock_session.return_value = AsyncMock()

        response = client.post(
            "/api/profiles",
            json={
                "name": "Wakacje Grecja",
                "countries": ["Grecja"],
                "budget_max": "3000",
            },
        )
        assert response.status_code == 201

    @patch("app.api.profiles.get_profile", new_callable=AsyncMock)
    @patch("app.api.profiles.get_session")
    def test_get_profile(self, mock_session, mock_get, client):
        profile = _mock_profile()
        mock_get.return_value = profile
        mock_session.return_value = AsyncMock()

        response = client.get(f"/api/profiles/{profile.id}")
        assert response.status_code == 200

    @patch("app.api.profiles.get_profile", new_callable=AsyncMock)
    @patch("app.api.profiles.get_session")
    def test_get_nonexistent_profile_404(self, mock_session, mock_get, client):
        mock_get.return_value = None
        mock_session.return_value = AsyncMock()

        response = client.get(f"/api/profiles/{uuid.uuid4()}")
        assert response.status_code == 404

    @patch("app.api.profiles.update_profile", new_callable=AsyncMock)
    @patch("app.api.profiles.get_session")
    def test_update_profile(self, mock_session, mock_update, client):
        profile = _mock_profile(name="Updated")
        mock_update.return_value = profile
        mock_session.return_value = AsyncMock()

        response = client.patch(
            f"/api/profiles/{profile.id}",
            json={"name": "Updated"},
        )
        assert response.status_code == 200

    @patch("app.api.profiles.delete_profile", new_callable=AsyncMock)
    @patch("app.api.profiles.get_session")
    def test_delete_profile(self, mock_session, mock_delete, client):
        mock_delete.return_value = True
        mock_session.return_value = AsyncMock()

        response = client.delete(f"/api/profiles/{uuid.uuid4()}")
        assert response.status_code == 204

    @patch("app.api.profiles.delete_profile", new_callable=AsyncMock)
    @patch("app.api.profiles.get_session")
    def test_delete_nonexistent_profile_404(self, mock_session, mock_delete, client):
        mock_delete.return_value = False
        mock_session.return_value = AsyncMock()

        response = client.delete(f"/api/profiles/{uuid.uuid4()}")
        assert response.status_code == 404


class TestAlertsAPI:
    def test_list_alerts_empty(self, client):
        session = AsyncMock()
        count_result = MagicMock()
        count_result.scalar_one.return_value = 0
        data_result = MagicMock()
        data_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(side_effect=[count_result, data_result])

        from app.database.session import get_session

        async def override_session():
            yield session

        app.dependency_overrides[get_session] = override_session
        try:
            response = client.get("/api/alerts")
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 0
            assert data["alerts"] == []
        finally:
            app.dependency_overrides.clear()

