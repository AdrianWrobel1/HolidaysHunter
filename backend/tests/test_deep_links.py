import logging
from app.models.enums import Provider
from app.providers.schemas import build_direct_offer_url
from app.providers.tui.normalizer import TuiNormalizer
from app.providers.rainbow.normalizer import RainbowNormalizer
from app.providers.wakacje_pl.normalizer import WakacjePlNormalizer
from app.providers.itaka.normalizer import ItakaNormalizer


class TestDeepLinks:
    """Comprehensive unit tests for direct offer deep links across all 4 providers.

    Verifies:
    1. Direct deep link usage for each provider (relative & absolute)
    2. Proper domain prepending for relative URLs (https://www.tui.pl, https://r.pl, https://www.wakacje.pl, https://www.itaka.pl)
    3. Preservation of full absolute URLs without modification
    4. Absence of fallbacks: returns None and logs detailed warning when deep link is missing.
    """

    def test_tui_relative_and_absolute_urls(self, caplog) -> None:
        normalizer = TuiNormalizer()

        # Relative path
        raw_rel = {
            "offerCode": "TUI-001",
            "name": "Hotel TUI",
            "countryName": "Hiszpania",
            "departureDate": "2026-09-01",
            "totalPrice": 3000,
            "pricePerAdult": 1500,
            "offerUrl": "/wypoczynek/hiszpania/majorka/hotel-tui/OfferCodeWS/TUI-001",
        }
        res_rel = normalizer.normalize(raw_rel)
        assert res_rel is not None
        assert res_rel.offer_url == "https://www.tui.pl/wypoczynek/hiszpania/majorka/hotel-tui/OfferCodeWS/TUI-001"

        # Absolute URL
        raw_abs = {
            "offerCode": "TUI-002",
            "name": "Hotel TUI 2",
            "countryName": "Hiszpania",
            "departureDate": "2026-09-01",
            "totalPrice": 3000,
            "pricePerAdult": 1500,
            "detailUrl": "https://www.tui.pl/wypoczynek/hiszpania/hotel-tui-2",
        }
        res_abs = normalizer.normalize(raw_abs)
        assert res_abs is not None
        assert res_abs.offer_url == "https://www.tui.pl/wypoczynek/hiszpania/hotel-tui-2"

        # Missing URL -> None + warning
        with caplog.at_level(logging.WARNING):
            raw_missing = {
                "offerCode": "TUI-003",
                "name": "Hotel TUI 3",
                "countryName": "Hiszpania",
                "departureDate": "2026-09-01",
                "totalPrice": 3000,
                "pricePerAdult": 1500,
            }
            res_missing = normalizer.normalize(raw_missing)
            assert res_missing is not None
            assert res_missing.offer_url is None
            assert "TUI" in caplog.text
            assert "TUI-003" in caplog.text

    def test_rainbow_oferta_url_and_fallbacks(self, caplog) -> None:
        normalizer = RainbowNormalizer()

        # Relative OfertaUrl (uppercase O)
        raw_rel = {
            "id": "R-100",
            "tytul": "Hotel Rainbow",
            "kraj": "Grecja",
            "dataWyjazdu": "2026-09-01",
            "cenaCalkowita": 4000,
            "cenaZaOsobe": 2000,
            "OfertaUrl": "/zakynthos-wczasy/katerina-studio?unikalnyKluczOferty=R-100",
        }
        res_rel = normalizer.normalize(raw_rel)
        assert res_rel is not None
        assert res_rel.offer_url == "https://r.pl/zakynthos-wczasy/katerina-studio?unikalnyKluczOferty=R-100"

        # Absolute URL
        raw_abs = {
            "id": "R-101",
            "tytul": "Hotel Rainbow 2",
            "kraj": "Grecja",
            "dataWyjazdu": "2026-09-01",
            "cenaCalkowita": 4000,
            "cenaZaOsobe": 2000,
            "url": "https://r.pl/grecja/hotel-rainbow-2",
        }
        res_abs = normalizer.normalize(raw_abs)
        assert res_abs is not None
        assert res_abs.offer_url == "https://r.pl/grecja/hotel-rainbow-2"

        # Missing URL -> None + warning
        with caplog.at_level(logging.WARNING):
            raw_missing = {
                "id": "R-102",
                "tytul": "Hotel Rainbow 3",
                "kraj": "Grecja",
                "dataWyjazdu": "2026-09-01",
                "cenaCalkowita": 4000,
                "cenaZaOsobe": 2000,
            }
            res_missing = normalizer.normalize(raw_missing)
            assert res_missing is not None
            assert res_missing.offer_url is None
            assert "RAINBOW" in caplog.text
            assert "R-102" in caplog.text

    def test_wakacje_pl_urls_and_missing_behavior(self, caplog) -> None:
        normalizer = WakacjePlNormalizer()

        # Relative path
        raw_rel = {
            "id": "W-500",
            "title": "Hotel Wakacje",
            "country": "Włochy",
            "departureDate": "2026-09-01",
            "priceTotal": 5000,
            "pricePerPerson": 2500,
            "url": "/wczasy/wlochy/sardynia/hotel-wakacje-500.html",
        }
        res_rel = normalizer.normalize(raw_rel)
        assert res_rel is not None
        assert res_rel.offer_url == "https://www.wakacje.pl/wczasy/wlochy/sardynia/hotel-wakacje-500.html"

        # urlName construction
        raw_urlname = {
            "id": "W-501",
            "title": "Hotel Wakacje 2",
            "country": "Włochy",
            "departureDate": "2026-09-01",
            "priceTotal": 5000,
            "pricePerPerson": 2500,
            "urlName": "oferty/hotel-wakacje-2-501.html",
        }
        res_urlname = normalizer.normalize(raw_urlname)
        assert res_urlname is not None
        assert res_urlname.offer_url == "https://www.wakacje.pl/oferty/hotel-wakacje-2-501.html"

        # Missing URL -> None + warning
        with caplog.at_level(logging.WARNING):
            raw_missing = {
                "id": "W-502",
                "title": "Hotel Wakacje 3",
                "country": "Włochy",
                "departureDate": "2026-09-01",
                "priceTotal": 5000,
                "pricePerPerson": 2500,
            }
            res_missing = normalizer.normalize(raw_missing)
            assert res_missing is not None
            assert res_missing.offer_url is None
            assert "WAKACJE_PL" in caplog.text
            assert "W-502" in caplog.text

    def test_itaka_urls_and_missing_behavior(self, caplog) -> None:
        normalizer = ItakaNormalizer()

        # Relative path
        raw_rel = {
            "offerId": "I-900",
            "title": "Hotel Itaka",
            "country": "Egipt",
            "departureDate": "2026-09-01",
            "price": 3500,
            "pricePerPerson": 1750,
            "url": "/wczasy/egipt/hurghada/hotel-itaka,900.html",
        }
        res_rel = normalizer.normalize(raw_rel)
        assert res_rel is not None
        assert res_rel.offer_url == "https://www.itaka.pl/wczasy/egipt/hurghada/hotel-itaka,900.html"

        # Absolute URL
        raw_abs = {
            "offerId": "I-901",
            "title": "Hotel Itaka 2",
            "country": "Egipt",
            "departureDate": "2026-09-01",
            "price": 3500,
            "pricePerPerson": 1750,
            "webUrl": "https://www.itaka.pl/wczasy/egipt/hotel-itaka-2",
        }
        res_abs = normalizer.normalize(raw_abs)
        assert res_abs is not None
        assert res_abs.offer_url == "https://www.itaka.pl/wczasy/egipt/hotel-itaka-2"

        # Missing URL -> None + warning
        with caplog.at_level(logging.WARNING):
            raw_missing = {
                "offerId": "I-902",
                "title": "Hotel Itaka 3",
                "country": "Egipt",
                "departureDate": "2026-09-01",
                "price": 3500,
                "pricePerPerson": 1750,
            }
            res_missing = normalizer.normalize(raw_missing)
            assert res_missing is not None
            assert res_missing.offer_url is None
            assert "ITAKA" in caplog.text
            assert "I-902" in caplog.text

    def test_build_direct_offer_url_direct_function(self, caplog) -> None:
        """Test build_direct_offer_url directly with various inputs."""
        # Absolute URLs
        assert build_direct_offer_url(Provider.TUI, "1", "https://www.tui.pl/offer") == "https://www.tui.pl/offer"
        assert build_direct_offer_url(Provider.RAINBOW, "2", "http://r.pl/offer") == "http://r.pl/offer"

        # Relative URLs
        assert build_direct_offer_url(Provider.ITAKA, "3", "/wczasy/123") == "https://www.itaka.pl/wczasy/123"
        assert build_direct_offer_url(Provider.WAKACJE_PL, "4", "wczasy/456") == "https://www.wakacje.pl/wczasy/456"

        # Missing URLs return None and log warning
        with caplog.at_level(logging.WARNING):
            assert build_direct_offer_url(Provider.TUI, "999", None) is None
            assert "999" in caplog.text
            assert "TUI" in caplog.text

        with caplog.at_level(logging.WARNING):
            assert build_direct_offer_url(Provider.RAINBOW, "888", "   ") is None
            assert "888" in caplog.text
