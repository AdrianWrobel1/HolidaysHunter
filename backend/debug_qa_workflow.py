"""Diagnostic execution script for QA system & scenario replication."""

import asyncio
from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from app.database.session import async_session_factory
from app.models.enums import Provider
from app.models.offer import Offer
from app.services.import_service import run_import
from app.services.offer_service import list_offers
from app.services.qa_service import debug_offer_by_id, get_latest_qa_report, run_qa_audit, validate_offer


async def main():
    print("================ STEP 1: CONFIRM QA DETECTS INVALID DATA ================")
    # Create intentional invalid offer payload (invalid country, missing price, invalid board)
    invalid_raw = {"country": "spain_unknown_raw", "provider": "invalid_provider_name"}
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

    print("\n================ STEP 2: REPLICATE SCENARIO (IMPORT & QA AUDIT) ================")
    # Clear DB & reimport sample offers
    async with async_session_factory() as session:
        await session.execute(delete(Offer))
        await session.commit()

    for provider in [Provider.ITAKA, Provider.TUI]:
        async with async_session_factory() as session:
            await run_import(provider, session)
            await session.commit()

    async with async_session_factory() as session:
        report = await run_qa_audit(session)
        print("\nQA Report Summary:")
        print(f"  Total imported: {report['summary']['total_imported']}")
        print(f"  Valid: {report['summary']['total_valid']}")
        print(f"  Invalid: {report['summary']['total_invalid']}")

        # Query 1: country=Hiszpania
        res_h, count_h = await list_offers(session, country="Hiszpania")
        print(f"\nQuery 1: country='Hiszpania' -> {count_h} offers found")

        # Query 2: provider='Itaka' (TitleCase passed from UI/user query)
        res_i, count_i = await list_offers(session, provider="Itaka")
        print(f"Query 2: provider='Itaka' -> {count_i} offers found")

        # Query 3: country='Hiszpania' + provider='Itaka'
        res_hi, count_hi = await list_offers(session, country="Hiszpania", provider="Itaka")
        print(f"Query 3: country='Hiszpania' + provider='Itaka' -> {count_hi} offers found")

        # Query 4: country='Hiszpania' + provider='itaka' (lowercase)
        res_hil, count_hil = await list_offers(session, country="Hiszpania", provider="itaka")
        print(f"Query 4: country='Hiszpania' + provider='itaka' (lowercase) -> {count_hil} offers found")

        # Use debug_offer_by_id on an Itaka offer to trace exact stage!
        stmt = select(Offer).where(Offer.provider == "itaka")
        itaka_offer = (await session.execute(stmt)).scalars().first()
        if itaka_offer:
            print(f"\nTracing single offer lineage for ID: {itaka_offer.external_id}...")
            debug_info = await debug_offer_by_id(session, itaka_offer.external_id)
            print(f"Lineage Debug Trace for {itaka_offer.external_id}:")
            for check in debug_info["lineage"]["4_filter_results"]:
                print(f"  [{check['status']}] Filter: {check['filter']} ({check['tested_value']}) -> {check['explanation']}")

if __name__ == "__main__":
    asyncio.run(main())
