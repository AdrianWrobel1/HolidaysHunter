import asyncio
from sqlalchemy import select
from app.database.session import async_session_factory
from app.models.offer import Offer

async def main():
    try:
        async with async_session_factory() as session:
            res = await session.execute(select(Offer))
            offers = res.scalars().all()
            print(f"Total DB offers: {len(offers)}")
            for o in offers:
                print(f"[{o.provider}] {o.external_id} | {o.hotel_name} | {o.offer_url}")
    except Exception as e:
        print(f"DB Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
