import asyncio
import sys
import os
from sqlalchemy import text, delete
import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.session import async_session_factory
from app.models.offer import Offer

async def run_step_8_and_9():
    print("=== PUNKT 8: STANY AKTUALNE W BAZIE DANYCH ===")
    async with async_session_factory() as session:
        count_res = await session.execute(text("SELECT COUNT(*) FROM offers"))
        count = count_res.scalar()
        print(f"SELECT COUNT(*) FROM offers: {count}")
        
        rows_res = await session.execute(text("SELECT external_id, offer_url FROM offers LIMIT 20"))
        rows = rows_res.fetchall()
        print("\n--- PIERWSZYCH 20 REKORDÓW ---")
        for idx, (ext_id, url) in enumerate(rows, 1):
            print(f"{idx:02d}. SELECT external_id: {ext_id} | SELECT offer_url: {url}")

    print("\n=== PUNKT 9: EXECUTE DELETE FROM offers; COMMIT; ===")
    async with async_session_factory() as session:
        await session.execute(delete(Offer))
        await session.commit()
    print("Wykonano DELETE FROM offers; COMMIT;")

    # Sprawdzenie bazy po usunięciu bezpośrednim zapytaniem SQL
    async with async_session_factory() as session:
        count_after = (await session.execute(text("SELECT COUNT(*) FROM offers"))).scalar()
        print(f"Liczba rekordów w bazie danych bezpośrednio po DELETE: {count_after}")

    # Zapytanie do endpointu przez HTTP / httpx (jeśli serwer działa) lub bezpośrednio przez wywołanie funkcji list_offers
    from app.services.offer_service import list_offers
    async with async_session_factory() as session:
        offers_from_service, total_from_service = await list_offers(session=session)
        print(f"\nLiczba ofert zwracana przez serwis DB (list_offers): {len(offers_from_service)}, total: {total_from_service}")
        print(f"Czy serwis/endpoint zwraca pustą listę? {'TAK' if len(offers_from_service) == 0 else 'NIE'}")

if __name__ == "__main__":
    asyncio.run(run_step_8_and_9())
