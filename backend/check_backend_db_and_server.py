import os
from sqlalchemy import select
from app.database.session import async_session_factory
from app.models.offer import Offer
from app.core.config import settings

async def check():
    print(f"DATABASE_URL in settings: {settings.DATABASE_URL}")
    async with async_session_factory() as session:
        res = await session.execute(select(Offer))
        offers = res.scalars().all()
        print(f"Total offers in DB: {len(offers)}")
        for o in offers[:20]:
            print(f"  [{o.provider}] {o.external_id} | {o.hotel_name} | {o.offer_url}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(check())
