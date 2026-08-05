import asyncio
from sqlalchemy import delete
from app.database.session import async_session_factory
from app.models.enums import Provider
from app.models.offer import Offer
from app.services.import_service import run_import

async def main():
    print("Clearing old offers from database...")
    async with async_session_factory() as session:
        await session.execute(delete(Offer))
        await session.commit()

    print("Running fresh import for all 4 providers...")
    for provider in [Provider.TUI, Provider.RAINBOW, Provider.WAKACJE_PL, Provider.ITAKA]:
        async with async_session_factory() as session:
            await run_import(provider, session)
            await session.commit()

    print("Checking newly imported database records...")
    async with async_session_factory() as session:
        from sqlalchemy import select
        res = await session.execute(select(Offer))
        offers = res.scalars().all()
        print(f"Total updated DB offers: {len(offers)}")
        for o in offers:
            print(f"[{o.provider.upper()}] ID: {o.external_id} | Hotel: {o.hotel_name} | URL: {o.offer_url}")

if __name__ == "__main__":
    asyncio.run(main())
