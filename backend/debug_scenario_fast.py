"""Fast diagnostic scenario replication script using sample offers."""

import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from app.database.session import async_session_factory
from app.models.enums import Provider
from app.models.offer import Offer
from app.services.offer_service import list_offers
from app.services.qa_service import debug_offer_by_id, run_qa_audit, validate_offer


async def main():
    print("================ STEP 1: CONFIRM QA DETECTS INVALID DATA ================")
    invalid_raw = {"country": "spain_raw", "provider": "invalid_provider_name"}
    invalid_db_offer = Offer(
        external_id="INVALID-001",
        provider="invalid_provider_name",
        title="Invalid Hotel Test",
        country="hiszpania",  # uncanonicalized string
        hotel_name="",       # empty hotel name
        departure_date=date(2026, 8, 20),
        return_date=date(2026, 8, 27),
        duration_nights=7,
        departure_city="UnknownAirport",
        meal_type="invalid_board",
        transport_type="flight",
        price_total=Decimal("1000.00"),
        price_per_person=Decimal("2000.00"),  # price_total < price_per_person error!
        is_available=True,
    )
    
    qa_errors = validate_offer(invalid_raw, None, offer_db=invalid_db_offer)
    print(f"QA Validation Errors detected for invalid offer ({len(qa_errors)} errors):")
    for err in qa_errors:
        print(f"  [FAIL] {err}")
    assert len(qa_errors) > 0, "QA must detect invalid offer errors!"

    print("\n================ STEP 2: REPLICATE SCENARIO WITH OFFERS ================")
    async with async_session_factory() as session:
        await session.execute(delete(Offer))
        await session.commit()

        # Seed 2 valid offers (1 Itaka Spain, 1 TUI Spain)
        itaka_offer = Offer(
            external_id="ITAKA-SPAIN-01",
            provider="itaka",
            title="Itaka Sol Hotel",
            country="Hiszpania",
            region="Majorka",
            city="Palma",
            hotel_name="Itaka Sol Hotel",
            hotel_stars=4.0,
            hotel_rating=8.5,
            departure_date=date(2026, 8, 20),
            return_date=date(2026, 8, 27),
            duration_nights=7,
            departure_city="Warszawa",
            adults=2,
            children=0,
            meal_type="all_inclusive",
            transport_type="flight",
            price_total=Decimal("6000.00"),
            price_per_person=Decimal("3000.00"),
            offer_url="https://www.itaka.pl/wczasy/hiszpania/itaka-sol-hotel",
            is_available=True,
        )
        tui_offer = Offer(
            external_id="TUI-SPAIN-02",
            provider="tui",
            title="TUI Magic Hotel",
            country="Hiszpania",
            region="Majorka",
            city="Palma",
            hotel_name="TUI Magic Hotel",
            hotel_stars=5.0,
            hotel_rating=9.0,
            departure_date=date(2026, 8, 20),
            return_date=date(2026, 8, 27),
            duration_nights=7,
            departure_city="Warszawa",
            adults=2,
            children=0,
            meal_type="all_inclusive",
            transport_type="flight",
            price_total=Decimal("7000.00"),
            price_per_person=Decimal("3500.00"),
            offer_url="https://www.tui.pl/wypoczynek/hiszpania/tui-magic-hotel",
            is_available=True,
        )
        session.add(itaka_offer)
        session.add(tui_offer)
        await session.commit()

    async with async_session_factory() as session:
        report = await run_qa_audit(session)

        # Scenario 1: country='Hiszpania'
        res_h, count_h = await list_offers(session, country="Hiszpania")
        print(f"\nResult 1: country='Hiszpania' -> {count_h} offers")

        # Scenario 2: provider='Itaka' (Titlecase as passed by UI/Endpoint query)
        res_i, count_i = await list_offers(session, provider="Itaka")
        print(f"Result 2: provider='Itaka' (TitleCase) -> {count_i} offers")

        # Scenario 3: country='Hiszpania' + provider='Itaka' (TitleCase)
        res_hi, count_hi = await list_offers(session, country="Hiszpania", provider="Itaka")
        print(f"Result 3: country='Hiszpania' + provider='Itaka' (TitleCase) -> {count_hi} offers")

        # Scenario 4: country='Hiszpania' + provider='itaka' (lowercase)
        res_hil, count_hil = await list_offers(session, country="Hiszpania", provider="itaka")
        print(f"Result 4: country='Hiszpania' + provider='itaka' (lowercase) -> {count_hil} offers")

        print("\n================ STEP 3: DEBUG OFFER WITH /debug/offer/ITAKA-SPAIN-01 ================")
        debug_res = await debug_offer_by_id(session, "ITAKA-SPAIN-01")
        print("Lineage filter check results for ITAKA-SPAIN-01:")
        for check in debug_res["lineage"]["4_filter_results"]:
            print(f"  [{check['status']}] Filter: {check['filter']} ({check['tested_value']}) -> {check['explanation']}")

if __name__ == "__main__":
    asyncio.run(main())
