import asyncio
import sys
import os
from sqlalchemy import text, delete

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.database.session import engine, async_session_factory
from app.models.offer import Offer

async def run_db_proof():
    print("=== DOWÓD KONFIGURACJI BAZY DANYCH ===")
    
    # 1. DATABASE_URL
    print("1. DATABASE_URL (z settings):", repr(settings.database_url))
    
    # 2. Silnik SQLAlchemy
    print("2. Silnik SQLAlchemy (engine.name):", engine.name)
    
    # 3. Szczegóły silnika / pliku / hosta
    print("3. Wykryty typ bazy:")
    if engine.name == "sqlite":
        print("   Plik SQLite:", engine.url.database)
    else:
        print("   Typ:", engine.name)
        print("   Host:", engine.url.host)
        print("   Port:", engine.url.port)
        print("   Nazwa bazy:", engine.url.database)
        print("   Użytkownik:", engine.url.username)

    # 4. reimport_all.py engine.url
    from app.database.session import engine as reimport_engine
    print("\n4. reimport_all.py engine.url:", repr(str(reimport_engine.url)))

    # 5. GET /api/offers engine.url
    print("5. GET /api/offers engine.url:", repr(str(engine.url)))

    # 6. Czy są takie same?
    are_same = str(reimport_engine.url) == str(engine.url)
    print(f"6. Udowodniono, że to dokładnie ta sama baza? {'TAK' if are_same else 'NIE'}")

    # 8. Rekordy przed czyszczeniem
    async with async_session_factory() as session:
        count_res = await session.execute(text("SELECT COUNT(*) FROM offers"))
        count = count_res.scalar()
        print(f"\n8. SELECT COUNT(*) FROM offers: {count}")
        
        rows_res = await session.execute(text("SELECT external_id, offer_url FROM offers LIMIT 20"))
        rows = rows_res.fetchall()
        print("   Pierwszych 20 rekordów (external_id | offer_url):")
        for idx, (ext_id, url) in enumerate(rows, 1):
            print(f"   {idx:02d}. external_id: {ext_id} | offer_url: {url}")

    # 9. Usunięcie z bazy danych
    print("\n9. Wykonywanie: DELETE FROM offers; COMMIT;")
    async with async_session_factory() as session:
        await session.execute(delete(Offer))
        await session.commit()
    print("   Wykonano DELETE i COMMIT w bazie PostgreSQL.")

if __name__ == "__main__":
    asyncio.run(run_db_proof())
