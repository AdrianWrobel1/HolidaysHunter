from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    @patch("app.api.health.check_database_connection", new_callable=AsyncMock)
    def test_returns_ok_when_database_is_available(self, mock_check, client):
        mock_check.return_value = True

        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "ok"}

    @patch("app.api.health.check_database_connection", new_callable=AsyncMock)
    def test_returns_503_when_database_is_unavailable(self, mock_check, client):
        mock_check.return_value = False

        response = client.get("/health")

        assert response.status_code == 503
        assert response.json() == {"status": "degraded", "database": "unavailable"}
