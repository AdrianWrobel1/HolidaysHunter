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

    def test_normalizes_complete_offer_with_explicit_id(self) -> None:
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

    def test_normalizes_schema_org_product_without_explicit_id(self) -> None:
        raw = {
            "@context": "https://schema.org",
            "@type": "Product",
            "brand": {"@type": "Brand", "name": "Rainbow Tours"},
            "description": "Wypoczynek • Hiszpania: Costa del Sol ",
            "image": "https://grafiki.r.pl/hotel/728/wakacje-i-wczasy-w-hotelu-playacalida-196756.jpg",
            "name": "Playacalida",
            "offers": {"@type": "Offer", "price": "3198", "priceCurrency": "PLN"},
            "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "5.4",
                "bestRating": 6,
                "reviewCount": 483,
            },
            "url": "https://r.pl/hiszpania-costa-del-sol-wczasy/playacalida",
        }
        result = self.normalizer.normalize(raw)

        assert result is not None
        assert result.external_id == "rpl:hiszpania-costa-del-sol-wczasy:playacalida"
        assert result.provider == Provider.RAINBOW
        assert result.hotel_name == "Playacalida"
        assert result.country == "Hiszpania"
        assert result.region == "Costa del Sol"
        assert result.price_total == Decimal("3198")
        assert result.price_per_person == Decimal("1599.00")
        assert result.hotel_rating == 5.4
        assert result.offer_url == "https://r.pl/hiszpania-costa-del-sol-wczasy/playacalida"
        assert result.image_url == "https://grafiki.r.pl/hotel/728/wakacje-i-wczasy-w-hotelu-playacalida-196756.jpg"

    def test_deterministic_id_stability(self) -> None:
        raw = {
            "name": "Evenia Zoraida Beach Resort",
            "description": "Wypoczynek • Hiszpania: Costa Almeria",
            "offers": {"price": "3866", "priceCurrency": "PLN"},
            "url": "https://r.pl/hiszpania-costa-almeria/evenia-zoraida-beach-resort",
        }
        first = self.normalizer.normalize(raw)
        second = self.normalizer.normalize(raw)

        assert first is not None and second is not None
        assert first.external_id == second.external_id
        assert first.external_id == "rpl:hiszpania-costa-almeria:evenia-zoraida-beach-resort"

    def test_deterministic_id_collision_prevention(self) -> None:
        raw1 = {
            "name": "Playacalida",
            "description": "Wypoczynek • Hiszpania: Costa del Sol",
            "offers": {"price": "3198"},
            "url": "https://r.pl/hiszpania-costa-del-sol-wczasy/playacalida",
        }
        raw2 = {
            "name": "Playacalida",
            "description": "Wypoczynek • Hiszpania: Costa Almeria",
            "offers": {"price": "3436"},
            "url": "https://r.pl/hiszpania-costa-almeria/playacalida",
        }
        res1 = self.normalizer.normalize(raw1)
        res2 = self.normalizer.normalize(raw2)

        assert res1 is not None and res2 is not None
        assert res1.external_id != res2.external_id
        assert res1.external_id == "rpl:hiszpania-costa-del-sol-wczasy:playacalida"
        assert res2.external_id == "rpl:hiszpania-costa-almeria:playacalida"

    def test_fallback_external_id_from_image_url(self) -> None:
        raw = {
            "name": "Hotel Without URL",
            "kraj": "Hiszpania",
            "cenaCalkowita": 3000,
            "image": "https://grafiki.r.pl/hotel/9921/hotel-photo.jpg",
        }
        res = self.normalizer.normalize(raw)

        assert res is not None
        assert res.external_id == "rpl:hotel:9921"

    def test_fallback_external_id_from_attribute_signature(self) -> None:
        raw = {
            "nazwaHotelu": "Unique Hotel",
            "kraj": "Grecja",
            "region": "Kreta",
            "liczbaNocy": 7,
            "cenaCalkowita": 2500,
        }
        res1 = self.normalizer.normalize(raw)
        res2 = self.normalizer.normalize(raw)

        assert res1 is not None and res2 is not None
        assert res1.external_id.startswith("rpl:hash:")
        assert res1.external_id == res2.external_id

    def test_returns_none_for_invalid_price(self) -> None:
        raw = self._make_raw_offer(cenaCalkowita=0)
        result = self.normalizer.normalize(raw)
        assert result is None

