"""Verify transport filter: run import and check DB for non-flight offers."""
import asyncio
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
)
logger = logging.getLogger("verify")


async def main() -> None:
    from app.database.session import async_session_factory
    from app.models.enums import Provider
    from app.services.import_service import run_import
    from sqlalchemy import text

    providers = list(Provider)
    print(f"\nRunning import for providers: {[p.value for p in providers]}")
    print("=" * 65)

    import_stats: dict[str, dict] = {}

    for prov in providers:
        print(f"\n>>> Starting import: {prov.value}")
        try:
            async with async_session_factory() as session:
                await run_import(prov, session)
                await session.commit()
            print(f"<<< Done: {prov.value}")
        except Exception as exc:
            print(f"!!! ERROR {prov.value}: {exc}")

    print("\n" + "=" * 65)
    print("DB VERIFICATION")
    print("=" * 65)

    async with async_session_factory() as session:
        r_total = await session.execute(text("SELECT COUNT(*) FROM offers"))
        total = r_total.scalar()

        r_flight = await session.execute(
            text("SELECT COUNT(*) FROM offers WHERE transport_type = 'flight'")
        )
        flight_count = r_flight.scalar()

        r_non_flight = await session.execute(
            text(
                "SELECT transport_type, COUNT(*) as cnt "
                "FROM offers "
                "WHERE transport_type != 'flight' "
                "GROUP BY transport_type "
                "ORDER BY cnt DESC"
            )
        )
        non_flight_rows = r_non_flight.fetchall()

    print(f"\nTotal offers in DB         : {total}")
    print(f"  -> transport_type=flight : {flight_count}")
    print(f"  -> transport_type!=flight: {len(non_flight_rows)} type(s)")

    if non_flight_rows:
        print("\n[FAIL] Non-flight offers found in DB:")
        for row in non_flight_rows:
            print(f"  transport_type={row[0]!r}  count={row[1]}")
    else:
        print("\n[PASS] Brak ofert z transport_type != 'flight' w tabeli offers.")
        print("       Filtr dziala poprawnie — do bazy trafiaja wylacznie oferty lotnicze.")


if __name__ == "__main__":
    asyncio.run(main())
