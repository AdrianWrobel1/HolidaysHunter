"""Integration tests for Research Workspace API endpoints."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_workspace_sessions_api():
    with TestClient(app) as client:
        response = client.get("/api/admin/workspace/sessions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Create new session
        create_resp = client.post(
            "/api/admin/workspace/sessions",
            json={"name": "Test Sesja Turcja 2026", "description": "Opis sesji"},
        )
        assert create_resp.status_code == 200
        session_data = create_resp.json()
        assert session_data["name"] == "Test Sesja Turcja 2026"


def test_workspace_items_and_comparison_api():
    with TestClient(app) as client:
        sessions_resp = client.get("/api/admin/workspace/sessions")
        session_id = sessions_resp.json()[0]["id"]

        # Add item 1
        item1_resp = client.post(
            "/api/admin/workspace/items",
            json={
                "session_id": session_id,
                "offer_url": "https://www.itaka.pl/wczasy/grecja/kreta/hotel-chania",
                "tags": ["Favorite"],
                "notes": ["Dobra lokalizacja"],
            },
        )
        assert item1_resp.status_code == 200
        item1 = item1_resp.json()
        assert item1["id"] is not None

        # Add item 2
        item2_resp = client.post(
            "/api/admin/workspace/items",
            json={
                "session_id": session_id,
                "offer_url": "https://www.tui.pl/wypoczynek/grecja/kreta/hotel-heraklion",
                "tags": ["Observe"],
            },
        )
        assert item2_resp.status_code == 200
        item2 = item2_resp.json()

        # Compare items
        comp_resp = client.post(
            "/api/admin/workspace/compare",
            json={"item_ids": [item1["id"], item2["id"]]},
        )
        assert comp_resp.status_code == 200
        comp_data = comp_resp.json()
        assert "matrix" in comp_data
        assert "upgrade_recommendation" in comp_data
