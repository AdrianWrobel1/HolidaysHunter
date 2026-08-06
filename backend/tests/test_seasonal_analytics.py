"""Unit & Integration tests for Seasonal Analytics V2 Redesign."""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.seasonal_service import get_seasonal_analytics


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_get_seasonal_analytics_empty_session():
    """Test get_seasonal_analytics when database session returns 0 matching offers."""
    mock_session = AsyncMock()

    # Total offers count query returns 0
    mock_count_res = MagicMock()
    mock_count_res.scalar.return_value = 0

    # Countries query returns empty list
    mock_countries_res = MagicMock()
    mock_countries_res.scalars().all.return_value = ["Hiszpania", "Grecja", "Egipt"]

    mock_session.execute.side_effect = [mock_count_res, mock_countries_res]

    analytics = await get_seasonal_analytics(mock_session, country="Narnia")

    assert analytics["total_offers_analyzed"] == 0
    assert analytics["diagnostics"]["has_data"] is False
    assert analytics["diagnostics"]["suggested_countries"] == ["Hiszpania", "Grecja", "Egipt"]


def test_seasonal_analytics_api_endpoint_success(client):
    """Test GET /api/offers/seasonal-analytics endpoint returning full dashboard response."""
    mock_payload = {
        "total_offers_analyzed": 12,
        "active_filters": {"country": "Hiszpania"},
        "executive_summary": {
            "cheapest_month": {"month": 5, "name": "Maj", "season": "Wiosna 🌸", "avg_price": 2380.0, "min_price": 1900.0},
            "most_expensive_month": {"month": 8, "name": "Sierpień", "season": "Lato ☀️", "avg_price": 4120.0},
            "potential_savings": {"amount": 1740.0, "percentage": 42.2},
            "best_value_month": {"month": 9, "name": "Wrzesień", "value_score": 88.5, "avg_price": 2550.0},
            "biggest_price_drop": {"description": "14 dni przed wylotem", "drop_amount": 1044.0, "drop_pct": 29.5},
        },
        "monthly_heatmap": [
            {
                "month": 5,
                "month_name": "Maj",
                "season": "Wiosna 🌸",
                "avg_price": 2380.0,
                "median_price": 2300.0,
                "min_price": 1900.0,
                "max_price": 3100.0,
                "p10": 2000.0,
                "p25": 2150.0,
                "p75": 2600.0,
                "p90": 2900.0,
                "offer_count": 5,
                "avg_deal_score": 85.0,
                "avg_value_score": 88.5,
                "price_level": "low",
            }
        ],
        "price_trends": [
            {
                "period": "Maj",
                "month": 5,
                "month_name": "Maj",
                "avg": 2380.0,
                "median": 2300.0,
                "min": 1900.0,
                "max": 3100.0,
                "p10": 2000.0,
                "p25": 2150.0,
                "p75": 2600.0,
                "p90": 2900.0,
                "count": 5,
            }
        ],
        "price_distribution": {
            "buckets": [{"range_min": 1900, "range_max": 2500, "label": "1900-2500 PLN", "count": 5}],
            "box_plot": {"min": 1900.0, "p25": 2150.0, "median": 2300.0, "p75": 2600.0, "max": 3100.0, "mean": 2380.0},
            "market_median": 2300.0,
            "best_deals_threshold": 2000.0,
        },
        "seasonality_score": {
            "score": 79,
            "level": "Wysoka Sezonowość",
            "description": "Wybór odpowiedniego miesiąca wyjazdu ma kluczowe znaczenie.",
        },
        "best_time_to_buy": {
            "recommendation": "BUY_NOW",
            "title": "Kupuj Teraz (Last Minute 🔥)",
            "explanation": "Aktualne ceny Last Minute są o ok. 25% niższe od średniej.",
            "estimated_savings_pct": 25.0,
            "lead_time_breakdown": [{"window": "Last Minute (<14 dni)", "avg_price": 2100.0, "count": 3}],
        },
        "regional_comparison": [
            {
                "country": "Hiszpania",
                "region": "Costa Brava",
                "avg_price": 2380.0,
                "median_price": 2300.0,
                "cheapest_month_name": "Maj",
                "most_expensive_month_name": "Sierpień",
                "seasonality_score": 79,
                "avg_deal_score": 85.0,
                "avg_value_score": 88.5,
                "offer_count": 5,
            }
        ],
        "provider_comparison": [
            {
                "provider": "itaka",
                "avg_price": 2380.0,
                "median_price": 2300.0,
                "avg_deal_score": 85.0,
                "avg_value_score": 88.5,
                "cheapest_month_name": "Maj",
                "offer_count": 5,
            }
        ],
        "transport_analysis": {
            "flight_avg_price": 2380.0,
            "self_transport_avg_price": 1400.0,
            "flight_premium": 980.0,
            "transport_split": {"flight": 5},
            "monthly_comparison": [{"month": 5, "month_name": "Maj", "flight_avg": 2380.0, "self_avg": 1400.0}],
        },
        "price_forecast": {
            "next_month_name": "Czerwiec",
            "expected_price": 2650.0,
            "confidence_pct": 82,
            "trend_direction": "↑",
            "summary": "Prognozowana średnia cena w Czerwiec wynosi ok. 2650 PLN.",
        },
        "smart_insights": ["Croatia is 48% cheaper in May."],
        "diagnostics": {
            "has_data": True,
            "reason": None,
            "conflicting_filters": [],
            "suggested_countries": [],
        },
    }

    from unittest.mock import MagicMock
    with patch("app.services.seasonal_service.get_seasonal_analytics", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_payload
        response = client.get("/api/offers/seasonal-analytics?country=Hiszpania")
        assert response.status_code == 200
        data = response.json()
        assert data["total_offers_analyzed"] == 12
        assert data["executive_summary"]["cheapest_month"]["name"] == "Maj"
        assert data["seasonality_score"]["score"] == 79
        assert data["transport_analysis"]["flight_premium"] == 980.0
