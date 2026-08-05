import asyncio
import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import async_session_factory

async def check_db_content():
    async with async_session_factory() as session:
        count_res = await session.execute(text("SELECT COUNT(*) FROM offers"))
        count = count_res.scalar()
        print(f"COUNT: {count}")
        
        rows_res = await session.execute(text("SELECT external_id, offer_url FROM offers LIMIT 20"))
        rows = rows_res.fetchall()
        for idx, (ext_id, url) in enumerate(rows, 1):
            print(f"{idx:02d}. {ext_id} | {url}")

if __name__ == "__main__":
    asyncio.run(check_db_content())
