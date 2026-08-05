from decimal import Decimal

from app.models.enums import MealType, Provider, TransportType
from app.providers.itaka.normalizer import ItakaNormalizer


class TestItakaNormalizer:
    def setup_method(self) -> None:
        self.normalizer = ItakaNormalizer()

    def _make_raw_offer(self, **overrides: object) -> dict:
        """Create a minimal valid raw offer, with optional field overrides."""
        base = {
            "offerId": "12345",
            "title": "Hotel Sunny Beach",
            "country": "Grecja",
            "region": "Kreta",
            "city": "Heraklion",
            "hotelName": "Hotel Sunny Beach",
            "hotelStars": 4,
            "hotelRating": 8.5,
            "departureDate": "2026-09-15",
            "returnDate": "2026-09-22",
            "duration": 7,
            "departureCity": "Warszawa",
            "adults": 2,
            "children": 0,
            "boardType": "all inclusive",
            "transportType": "samolot",
            "price": 4200,
            "pricePerPerson": 2100,
            "url": "/oferta/12345",
            "imageUrl": "https://images.itaka.pl/photo.jpg",
        }
        base.update(overrides)
        return base

    def test_normalizes_complete_offer(self) -> None:
        raw = self._make_raw_offer()
        result = self.normalizer.normalize(raw)

        assert result is not None
        assert result.external_id == "12345"
        assert result.provider == Provider.ITAKA
        assert result.title == "Hotel Sunny Beach"
        assert result.country == "Grecja"
        assert result.region == "Kreta"
        assert result.hotel_name == "Hotel Sunny Beach"
        assert result.hotel_stars == 4.0
        assert result.hotel_rating == 8.5
        assert result.departure_date.isoformat() == "2026-09-15"
        assert result.return_date.isoformat() == "2026-09-22"
        assert result.duration_nights == 7
        assert result.departure_city == "Warszawa"
        assert result.adults == 2
        assert result.children == 0
        assert result.meal_type == MealType.ALL_INCLUSIVE
        assert result.transport_type == TransportType.FLIGHT
        assert result.price_total == Decimal("4200")
        assert result.price_per_person == Decimal("2100")
        assert result.offer_url == "https://www.itaka.pl/oferta/12345"
        assert result.image_url == "https://images.itaka.pl/photo.jpg"

    def test_returns_none_for_missing_id(self) -> None:
        raw = self._make_raw_offer()
        del raw["offerId"]
        result = self.normalizer.normalize(raw)
        assert result is None

    def test_returns_none_for_missing_price(self) -> None:
        raw = self._make_raw_offer()
        del raw["price"]
        result = self.normalizer.normalize(raw)
        assert result is None

    def test_returns_none_for_zero_price(self) -> None:
        raw = self._make_raw_offer(price=0)
        result = self.normalizer.normalize(raw)
        assert result is None

    def test_returns_none_for_missing_departure_date(self) -> None:
        raw = self._make_raw_offer()
        del raw["departureDate"]
        result = self.normalizer.normalize(raw)
        assert result is None

    def test_calculates_per_person_price_when_missing(self) -> None:
        raw = self._make_raw_offer(adults=2, children=1, price=6000)
        del raw["pricePerPerson"]
        result = self.normalizer.normalize(raw)

        assert result is not None
        assert result.price_per_person == Decimal("2000.00")

    def test_calculates_return_date_when_missing(self) -> None:
        raw = self._make_raw_offer(duration=10)
        del raw["returnDate"]
        result = self.normalizer.normalize(raw)

        assert result is not None
        assert result.return_date.isoformat() == "2026-09-25"

    def test_resolves_polish_meal_types(self) -> None:
        for meal_str, expected in [
            ("śniadania", MealType.BED_AND_BREAKFAST),
            ("pełne wyżywienie", MealType.FULL_BOARD),
            ("bez wyżywienia", MealType.SELF_CATERING),
        ]:
            raw = self._make_raw_offer(boardType=meal_str)
            result = self.normalizer.normalize(raw)
            assert result is not None
            assert result.meal_type == expected, f"Failed for '{meal_str}'"

    def test_resolves_polish_transport_types(self) -> None:
        for transport_str, expected in [
            ("samolot", TransportType.FLIGHT),
            ("autokar", TransportType.BUS),
            ("dojazd własny", TransportType.OWN),
        ]:
            raw = self._make_raw_offer(transportType=transport_str)
            result = self.normalizer.normalize(raw)
            assert result is not None
            assert result.transport_type == expected, f"Failed for '{transport_str}'"

    def test_prepends_base_url_to_relative_path(self) -> None:
        raw = self._make_raw_offer(url="/oferta/abc")
        result = self.normalizer.normalize(raw)
        assert result is not None
        assert result.offer_url == "https://www.itaka.pl/oferta/abc"

    def test_absolute_url_preserved(self) -> None:
        raw = self._make_raw_offer(url="https://www.itaka.pl/oferta/xyz")
        result = self.normalizer.normalize(raw)
        assert result is not None
        assert result.offer_url == "https://www.itaka.pl/oferta/xyz"

    def test_handles_alternative_field_names(self) -> None:
        """Test that the normalizer handles Itaka's alternate response keys."""
        raw = {
            "id": "99999",
            "title": "Alt Hotel",
            "country": "Egipt",
            "hotel": {"name": "Alt Hotel", "stars": 5, "rating": 9.0},
            "dateFrom": "2026-10-01",
            "dateTo": "2026-10-08",
            "nights": 7,
            "departureFrom": "Kraków",
            "adults": 2,
            "children": 0,
            "mealType": "hb",
            "transport": "flight",
            "priceTotal": 5000,
            "pricePerPerson": 2500,
            "offerUrl": "https://www.itaka.pl/oferta/99999",
        }
        result = self.normalizer.normalize(raw)

        assert result is not None
        assert result.external_id == "99999"
        assert result.hotel_name == "Alt Hotel"
        assert result.hotel_stars == 5.0
        assert result.hotel_rating == 9.0
        assert result.departure_date.isoformat() == "2026-10-01"
        assert result.departure_city == "Kraków"
        assert result.meal_type == MealType.HALF_BOARD
        assert result.transport_type == TransportType.FLIGHT

    def test_returns_none_offer_url_when_missing(self) -> None:
        """Test that missing offer_url in raw response results in offer_url=None."""
        raw = self._make_raw_offer()
        del raw["url"]
        result = self.normalizer.normalize(raw)
        assert result is not None
        assert result.offer_url is None


