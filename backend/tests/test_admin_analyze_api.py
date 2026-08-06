"""Integration tests for POST /api/admin/analyze-offer endpoint."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_analyze_offer_endpoint_success():
    with TestClient(app) as client:
        payload = {
            "url": "https://www.tui.pl/wypoczynek/hiszpania/teneryfa/hotel-bahia-principe"
        }

        response = client.post("/api/admin/analyze-offer", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "target_offer" in data
        assert "deal_score" in data
        assert "statistics" in data
        assert "market_position" in data
        assert "recommendation" in data
        assert "charts" in data
        assert data["target_offer"]["provider"].lower() == "tui"


def test_analyze_offer_endpoint_validation_error():
    with TestClient(app) as client:
        response = client.post("/api/admin/analyze-offer", json={"url": ""})
        assert response.status_code == 400
