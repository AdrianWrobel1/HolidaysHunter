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

    def test_normalizes_live_production_next_data_structure(self) -> None:
        live_raw = {
            "offerCode": "AYT43083",
            "hotelName": "Sun City Apartments & Hotel",
            "hotelStandard": 3.5,
            "tripAdvisorRating": 3.9,
            "discountPerPersonPrice": 958,
            "discountFullPrice": 1916,
            "departureDate": "12.12.2026",
            "returnDate": "19.12.2026",
            "durationNights": 7,
            "departureAirport": "Katowice",
            "boardType": "Bez wyżywienia",
            "participants": "2 Dorosłych + 0 Dzieci",
            "breadcrumbs": [
                {"label": "Turcja"},
                {"label": "Riwiera Turecka"}
            ],
            "imageUrl": "https://r.cdn.redgalaxy.com/scale/o2/TUI/hotels/AYT43083/S24/25247810.jpg",
            "offerUrl": "/wypoczynek/turcja/riwiera-turecka/sun-city-apartments-hotel-ayt43083"
        }
        result = self.normalizer.normalize(live_raw)

        assert result is not None
        assert result.external_id == "AYT43083"
        assert result.provider == Provider.TUI
        assert result.hotel_name == "Sun City Apartments & Hotel"
        assert result.country == "Turcja"
        assert result.region == "Riwiera Turecka"
        assert result.hotel_stars == 3.5
        assert result.hotel_rating == 3.9
        assert result.price_per_person == Decimal("958")
        assert result.price_total == Decimal("1916")
        assert result.departure_date.isoformat() == "2026-12-12"
        assert result.return_date.isoformat() == "2026-12-19"
        assert result.departure_city == "Katowice"
        assert result.adults == 2
        assert result.children == 0
        assert result.meal_type == MealType.SELF_CATERING
        assert result.offer_url == "https://www.tui.pl/wypoczynek/turcja/riwiera-turecka/sun-city-apartments-hotel-ayt43083"
        assert result.image_url == "https://r.cdn.redgalaxy.com/scale/o2/TUI/hotels/AYT43083/S24/25247810.jpg"

    def test_returns_none_for_missing_id(self) -> None:
        raw = self._make_raw_offer()
        del raw["offerCode"]
        result = self.normalizer.normalize(raw)
        assert result is None

    def test_returns_none_for_invalid_price(self) -> None:
        raw = self._make_raw_offer(totalPrice=0)
        result = self.normalizer.normalize(raw)
        assert result is None
