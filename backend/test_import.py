import asyncio
import logging
from unittest.mock import AsyncMock, patch

from sqlalchemy import select

from app.database.session import async_session_factory
from app.models.enums import Provider
from app.models.offer import Offer
from app.models.price_history import PriceHistory
from app.providers.itaka.provider import ItakaProvider
from app.providers.rainbow.provider import RainbowProvider
from app.providers.tui.provider import TuiProvider
from app.providers.wakacje_pl.provider import WakacjePlProvider
from app.services.import_service import run_import

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OFFER_SAMPLES = {
    Provider.ITAKA: [
        {
            "offerId": "ITAKA-101",
            "title": "Itaka Sunny Hotel",
            "country": "Grecja",
            "region": "Kreta",
            "hotelName": "Itaka Sunny Hotel",
            "departureDate": "2026-09-10",
            "price": 5000,
            "pricePerPerson": 2500,
        }
    ],
    Provider.TUI: [
        {
            "offerCode": "TUI-202",
            "name": "TUI Blue Resort",
            "countryName": "Hiszpania",
            "regionName": "Majorka",
            "hotelName": "TUI Blue Resort",
            "departureDate": "2026-08-20",
            "totalPrice": 6000,
            "pricePerAdult": 3000,
        }
    ],
    Provider.RAINBOW: [
        {
            "id": "RAINBOW-303",
            "tytul": "Rainbow Palace",
            "kraj": "Turcja",
            "region": "Antalya",
            "nazwaHotelu": "Rainbow Palace",
            "dataWyjazdu": "2026-09-05",
            "cenaCalkowita": 4400,
            "cenaZaOsobe": 2200,
        }
    ],
    Provider.WAKACJE_PL: [
        {
            "id": "WAKACJE-404",
            "title": "Wakacje Grand Hotel",
            "country": "Egipt",
            "region": "Hurghada",
            "hotelName": "Wakacje Grand Hotel",
            "departureDate": "2026-10-01",
            "priceTotal": 5200,
            "pricePerPerson": 2600,
        }
    ],
}


async def test_import_all_providers():
    print("\n=======================================================")
    print("   RUNNING ALL PROVIDERS IMPORT PIPELINE VERIFICATION")
    print("=======================================================\n")

    provider_classes = {
        Provider.ITAKA: ItakaProvider,
        Provider.TUI: TuiProvider,
        Provider.RAINBOW: RainbowProvider,
        Provider.WAKACJE_PL: WakacjePlProvider,
    }

    # 1. Run Import for each provider
    for provider, sample_data in OFFER_SAMPLES.items():
        cls = provider_classes[provider]
        print(f"--> Running import for {provider.value.upper()}...")
        async with async_session_factory() as session:
            with patch.object(
                cls,
                "fetch_offers",
                new_callable=AsyncMock,
                return_value=sample_data,
            ):
                await run_import(provider, session)
                await session.commit()

    # 2. Verify all records in PostgreSQL
    print("\n--> Verifying database records for all providers...")
    async with async_session_factory() as session:
        stmt = select(Offer)
        result = await session.execute(stmt)
        all_offers = result.scalars().all()

        print(f"    Total offers in PostgreSQL: {len(all_offers)}")
        for offer in all_offers:
            print(
                f"    [OK] [{offer.provider.upper()}] ID: {offer.external_id} | "
                f"Hotel: {offer.hotel_name} | Price: {offer.price_total} {offer.currency}"
            )

        stmt_hist = select(PriceHistory)
        result_hist = await session.execute(stmt_hist)
        all_hist = result_hist.scalars().all()
        print(f"\n    Total PriceHistory entries in PostgreSQL: {len(all_hist)}")

        assert len(all_offers) >= 4, "Expected at least 4 offers in database!"
        assert len(all_hist) >= 4, "Expected at least 4 price history records!"

    print("\n=======================================================")
    print("   [SUCCESS] ALL 4 OPERATORS VERIFIED & SAVED IN DB!  ")
    print("=======================================================\n")


if __name__ == "__main__":
    asyncio.run(test_import_all_providers())
