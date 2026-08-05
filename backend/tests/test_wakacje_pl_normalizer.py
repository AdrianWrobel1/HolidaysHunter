from decimal import Decimal

from app.models.enums import MealType, Provider, TransportType
from app.providers.wakacje_pl.normalizer import WakacjePlNormalizer


class TestWakacjePlNormalizer:
    def setup_method(self) -> None:
        self.normalizer = WakacjePlNormalizer()

    def _make_raw_offer(self, **overrides: object) -> dict:
        base = {
            "id": "WAKACJE-5544",
            "title": "Hotel Grand Wakacje",
            "country": "Włochy",
            "region": "Sardynia",
            "city": "Cagliari",
            "hotelName": "Hotel Grand Wakacje",
            "hotelStars": 4.5,
            "hotelRating": 9.4,
            "departureDate": "2026-09-12",
            "returnDate": "2026-09-19",
            "durationNights": 7,
            "departureCity": "Katowice",
            "adults": 2,
            "children": 0,
            "mealType": "hb",
            "transportType": "flight",
            "priceTotal": 6400,
            "pricePerPerson": 3200,
            "url": "/wlochy/sardynia/hotel-grand-wakacje",
            "imageUrl": "https://www.wakacje.pl/grand.jpg",
        }
        base.update(overrides)
        return base

    def test_normalizes_complete_offer(self) -> None:
        raw = self._make_raw_offer()
        result = self.normalizer.normalize(raw)

        assert result is not None
        assert result.external_id == "WAKACJE-5544"
        assert result.provider == Provider.WAKACJE_PL
        assert result.title == "Hotel Grand Wakacje"
        assert result.country == "Włochy"
        assert result.region == "Sardynia"
        assert result.hotel_name == "Hotel Grand Wakacje"
        assert result.hotel_stars == 4.5
        assert result.hotel_rating == 9.4
        assert result.departure_date.isoformat() == "2026-09-12"
        assert result.return_date.isoformat() == "2026-09-19"
        assert result.duration_nights == 7
        assert result.departure_city == "Katowice"
        assert result.adults == 2
        assert result.children == 0
        assert result.meal_type == MealType.HALF_BOARD
        assert result.transport_type == TransportType.FLIGHT
        assert result.price_total == Decimal("6400")
        assert result.price_per_person == Decimal("3200")
        assert result.offer_url == "https://www.wakacje.pl/wlochy/sardynia/hotel-grand-wakacje"
        assert result.image_url == "https://www.wakacje.pl/grand.jpg"

    def test_returns_none_for_missing_id(self) -> None:
        raw = self._make_raw_offer()
        del raw["id"]
        result = self.normalizer.normalize(raw)
        assert result is None

    def test_returns_none_for_invalid_price(self) -> None:
        raw = self._make_raw_offer(priceTotal=0)
        result = self.normalizer.normalize(raw)
        assert result is None
