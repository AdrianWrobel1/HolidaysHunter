import asyncio
import sys
import os
from sqlalchemy import select

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import async_session_factory
from app.models.offer import Offer

async def main():
    try:
        async with async_session_factory() as session:
            res = await session.execute(select(Offer))
            offers = res.scalars().all()
            print(f"Total DB offers: {len(offers)}")
            for o in offers:
                print(f"ID: {o.id} | Provider: {o.provider} | ExternalID: {o.external_id} | Hotel: {o.hotel_name} | URL: {o.offer_url}")
    except Exception as e:
        print(f"DB Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
