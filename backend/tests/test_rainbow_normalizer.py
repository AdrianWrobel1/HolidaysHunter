from decimal import Decimal

from app.models.enums import MealType, Provider, TransportType
from app.providers.rainbow.normalizer import RainbowNormalizer


class TestRainbowNormalizer:
    def setup_method(self) -> None:
        self.normalizer = RainbowNormalizer()

    def _make_raw_offer(self, **overrides: object) -> dict:
        base = {
            "id": "RAINBOW-7788",
            "tytul": "Hotel Rainbow Resort",
            "kraj": "Grecja",
            "region": "Rhodes",
            "miasto": "Faliraki",
            "nazwaHotelu": "Hotel Rainbow Resort",
            "standardHotelu": 4,
            "ocenaHotelu": 8.8,
            "dataWyjazdu": "2026-09-01",
            "dataPowrotu": "2026-09-08",
            "liczbaNocy": 7,
            "miastoWylotu": "Gdańsk",
            "dorosli": 2,
            "dzieci": 0,
            "wyzywienie": "all inclusive",
            "transport": "samolot",
            "cenaCalkowita": 4800,
            "cenaZaOsobe": 2400,
            "url": "/grecja/rhodes/hotel-rainbow-resort",
            "zdjecieGlowne": "https://r.pl/photo.jpg",
        }
        base.update(overrides)
        return base

    def test_normalizes_complete_offer(self) -> None:
        raw = self._make_raw_offer()
        result = self.normalizer.normalize(raw)

        assert result is not None
        assert result.external_id == "RAINBOW-7788"
        assert result.provider == Provider.RAINBOW
        assert result.title == "Hotel Rainbow Resort"
        assert result.country == "Grecja"
        assert result.region == "Rhodes"
        assert result.hotel_name == "Hotel Rainbow Resort"
        assert result.hotel_stars == 4.0
        assert result.hotel_rating == 8.8
        assert result.departure_date.isoformat() == "2026-09-01"
        assert result.return_date.isoformat() == "2026-09-08"
        assert result.duration_nights == 7
        assert result.departure_city == "Gdańsk"
        assert result.adults == 2
        assert result.children == 0
        assert result.meal_type == MealType.ALL_INCLUSIVE
        assert result.transport_type == TransportType.FLIGHT
        assert result.price_total == Decimal("4800")
        assert result.price_per_person == Decimal("2400")
        assert result.offer_url == "https://r.pl/grecja/rhodes/hotel-rainbow-resort"
        assert result.image_url == "https://r.pl/photo.jpg"

    def test_returns_none_for_missing_id(self) -> None:
        raw = self._make_raw_offer()
        del raw["id"]
        result = self.normalizer.normalize(raw)
        assert result is None

    def test_returns_none_for_invalid_price(self) -> None:
        raw = self._make_raw_offer(cenaCalkowita=0)
        result = self.normalizer.normalize(raw)
        assert result is None
