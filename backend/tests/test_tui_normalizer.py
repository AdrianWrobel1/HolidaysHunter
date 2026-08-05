from decimal import Decimal

from app.models.enums import MealType, Provider, TransportType
from app.providers.tui.normalizer import TuiNormalizer


class TestTuiNormalizer:
    def setup_method(self) -> None:
        self.normalizer = TuiNormalizer()

    def _make_raw_offer(self, **overrides: object) -> dict:
        base = {
            "offerCode": "TUI-12345",
            "name": "TUI BLUE Magic Life",
            "countryName": "Hiszpania",
            "regionName": "Majorka",
            "cityName": "Palma",
            "hotelName": "TUI BLUE Magic Life",
            "category": 5,
            "score": 9.1,
            "departureDate": "2026-08-20",
            "returnDate": "2026-08-27",
            "durationNights": 7,
            "departureAirport": "Poznań",
            "adultCount": 2,
            "childCount": 0,
            "boardName": "All Inclusive",
            "transportation": "FLIGHT",
            "totalPrice": 5600,
            "pricePerAdult": 2800,
            "detailUrl": "/oferty/tui-blue-12345",
            "pictureUrl": "https://images.tui.pl/magic.jpg",
        }
        base.update(overrides)
        return base

    def test_normalizes_complete_offer(self) -> None:
        raw = self._make_raw_offer()
        result = self.normalizer.normalize(raw)

        assert result is not None
        assert result.external_id == "TUI-12345"
        assert result.provider == Provider.TUI
        assert result.title == "TUI BLUE Magic Life"
        assert result.country == "Hiszpania"
        assert result.region == "Majorka"
        assert result.hotel_name == "TUI BLUE Magic Life"
        assert result.hotel_stars == 5.0
        assert result.hotel_rating == 9.1
        assert result.departure_date.isoformat() == "2026-08-20"
        assert result.return_date.isoformat() == "2026-08-27"
        assert result.duration_nights == 7
        assert result.departure_city == "Poznań"
        assert result.adults == 2
        assert result.children == 0
        assert result.meal_type == MealType.ALL_INCLUSIVE
        assert result.transport_type == TransportType.FLIGHT
        assert result.price_total == Decimal("5600")
        assert result.price_per_person == Decimal("2800")
        assert result.offer_url == "https://www.tui.pl/oferty/tui-blue-12345"
        assert result.image_url == "https://images.tui.pl/magic.jpg"

    def test_returns_none_for_missing_id(self) -> None:
        raw = self._make_raw_offer()
        del raw["offerCode"]
        result = self.normalizer.normalize(raw)
        assert result is None

    def test_returns_none_for_invalid_price(self) -> None:
        raw = self._make_raw_offer(totalPrice=0)
        result = self.normalizer.normalize(raw)
        assert result is None
