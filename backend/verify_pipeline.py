import asyncio
import json
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy import select
from fastapi.testclient import TestClient

from app.database.session import async_session_factory
from app.models.enums import Provider
from app.models.offer import Offer
from app.providers.tui.normalizer import TuiNormalizer
from app.providers.rainbow.normalizer import RainbowNormalizer
from app.providers.wakacje_pl.normalizer import WakacjePlNormalizer
from app.providers.itaka.normalizer import ItakaNormalizer
from app.services.import_service import run_import
from app.main import app

SAMPLES = {
    Provider.TUI: {
        "offerCode": "TUI-PL-2026-001",
        "name": "TUI BLUE Magic Life Palma",
        "countryName": "Hiszpania",
        "regionName": "Majorka",
        "cityName": "Palma de Mallorca",
        "hotelName": "TUI BLUE Magic Life Palma",
        "category": 5,
        "score": 9.2,
        "departureDate": "2026-08-20",
        "returnDate": "2026-08-27",
        "durationNights": 7,
        "departureAirport": "Warszawa",
        "adultCount": 2,
        "childCount": 0,
        "boardName": "All Inclusive",
        "transportation": "FLIGHT",
        "totalPrice": 6200,
        "pricePerAdult": 3100,
        "offerUrl": "/wypoczynek/hiszpania/majorka/palma-de-mallorca/tui-blue-magic-life-palma/OfferCodeWS/TUI-PL-2026-001",
    },
    Provider.RAINBOW: {
        "id": "RAINBOW-PL-2026-002",
        "tytul": "Hotel Katerina Studio",
        "kraj": "Grecja",
        "region": "Zakynthos",
        "miasto": "Laganas",
        "nazwaHotelu": "Katerina Studio",
        "standardHotelu": 4,
        "ocenaHotelu": 8.7,
        "dataWyjazdu": "2026-09-01",
        "dataPowrotu": "2026-09-08",
        "liczbaNocy": 7,
        "miastoWylotu": "Katowice",
        "dorosli": 2,
        "dzieci": 0,
        "wyzywienie": "all inclusive",
        "transport": "samolot",
        "cenaCalkowita": 4600,
        "cenaZaOsobe": 2300,
        "OfertaUrl": "/zakynthos-wczasy/katerina-studio?unikalnyKluczOferty=RAINBOW-PL-2026-002",
    },
    Provider.WAKACJE_PL: {
        "id": "WAKACJE-PL-2026-003",
        "title": "Steigenberger Resort Ras Soma",
        "country": "Egipt",
        "region": "Hurghada",
        "city": "Safaga",
        "hotelName": "Steigenberger Resort Ras Soma",
        "hotelStars": 5.0,
        "hotelRating": 9.5,
        "departureDate": "2026-10-05",
        "returnDate": "2026-10-12",
        "durationNights": 7,
        "departureCity": "Poznań",
        "adults": 2,
        "children": 0,
        "mealType": "all_inclusive",
        "transportType": "flight",
        "priceTotal": 7400,
        "pricePerPerson": 3700,
        "offerUrl": "/wczasy/egipt/hurghada/steigenberger-resort-ras-soma,WAKACJE-PL-2026-003.html",
    },
    Provider.ITAKA: {
        "offerId": "ITAKA-PL-2026-004",
        "title": "Hotel Creta Maris Resort",
        "country": "Grecja",
        "region": "Kreta",
        "city": "Hersonissos",
        "hotelName": "Hotel Creta Maris Resort",
        "hotelStars": 5.0,
        "hotelRating": 9.1,
        "departureDate": "2026-09-15",
        "returnDate": "2026-09-22",
        "duration": 7,
        "departureCity": "Wrocław",
        "adults": 2,
        "children": 0,
        "boardType": "all inclusive",
        "transportType": "samolot",
        "price": 6800,
        "pricePerPerson": 3400,
        "url": "/wczasy/grecja/kreta/hotel-creta-maris-resort,ITAKA-PL-2026-004.html",
    },
}

NORMALIZERS = {
    Provider.TUI: TuiNormalizer(),
    Provider.RAINBOW: RainbowNormalizer(),
    Provider.WAKACJE_PL: WakacjePlNormalizer(),
    Provider.ITAKA: ItakaNormalizer(),
}

PROVIDER_DOMAINS = {
    "itaka": "https://www.itaka.pl",
    "tui": "https://www.tui.pl",
    "rainbow": "https://r.pl",
    "wakacje_pl": "https://www.wakacje.pl",
}

def resolve_frontend_url(provider: str, offer_url: str | None) -> str | None:
    if not offer_url or not offer_url.strip():
        return None
    url = offer_url.strip()
    if url.startswith("http://") or url.startswith("https://"):
        return url
    domain = PROVIDER_DOMAINS.get(provider.lower())
    if domain:
        return f"{domain}{url if url.startswith('/') else '/' + url}"
    return url

async def main():
    report = {}

    for provider, sample_data in SAMPLES.items():
        prov_key = provider.value
        report[prov_key] = {}

        # 1. Raw API snippet
        raw_url_field = (
            sample_data.get("offerUrl")
            or sample_data.get("OfertaUrl")
            or sample_data.get("url")
        )
        url_key = "offerUrl" if "offerUrl" in sample_data else ("OfertaUrl" if "OfertaUrl" in sample_data else "url")
        report[prov_key]["1_raw_api_snippet"] = {
            "offer_id": sample_data.get("offerCode") or sample_data.get("id") or sample_data.get("offerId"),
            url_key: raw_url_field,
        }

        # 2. NormalizedOffer
        normalizer = NORMALIZERS[provider]
        normalized = normalizer.normalize(sample_data)
        report[prov_key]["2_normalized_offer"] = {
            "external_id": normalized.external_id,
            "provider": normalized.provider.value,
            "hotel_name": normalized.hotel_name,
            "offer_url": normalized.offer_url,
        }

        # 3. Database Record
        async with async_session_factory() as session:
            with patch("app.services.import_service.get_provider_entry") as mock_entry:
                mock_p = AsyncMock()
                mock_p.fetch_offers.return_value = [sample_data]
                mock_p.close = AsyncMock()
                mock_e = MagicMock()
                mock_e.create_provider.return_value = mock_p
                mock_e.create_normalizer.return_value = normalizer
                mock_entry.return_value = mock_e

                await run_import(provider, session)
                await session.commit()

            stmt = select(Offer).where(
                Offer.provider == prov_key,
                Offer.external_id == normalized.external_id,
            )
            db_offer = (await session.execute(stmt)).scalar_one()
            report[prov_key]["3_db_record"] = {
                "id": str(db_offer.id),
                "external_id": db_offer.external_id,
                "provider": db_offer.provider,
                "offer_url": db_offer.offer_url,
            }

        # 4. REST API Endpoint Response Schema (OfferResponse)
        from app.api.schemas import OfferResponse
        api_offer = OfferResponse.model_validate(db_offer)
        report[prov_key]["4_rest_api_response"] = {
            "id": str(api_offer.id),
            "provider": api_offer.provider,
            "offer_url": api_offer.offer_url,
        }

        # 5. Frontend value
        frontend_value = resolve_frontend_url(api_offer.provider, api_offer.offer_url)
        report[prov_key]["5_frontend_resolved_url"] = frontend_value

    print(json.dumps(report, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
