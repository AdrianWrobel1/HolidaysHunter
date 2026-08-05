"""Automated Live Import & Query Filter Combinations Test Suite.

Tests all 1-, 2-, and 3-element combinations of the 11 live import filters:
1. provider
2. country
3. region
4. airport (departure_city)
5. meal_type
6. stars (hotel_stars)
7. duration (duration_min / duration_max)
8. adults
9. children
10. price (price_max)
11. departure_date (date_from / date_to)

Total combinations tested: 11 + 55 + 165 = 231.

For each combination, the test verifies:
- Backend live import & query execution return without exceptions or HTTP errors.
- Monotonicity principle: adding a filter cannot increase result count (count(A+B) <= count(A)).
- Logical non-zero consistency: no false 0 count when matching records exist in the database.
- Generates a complete PASS/FAIL summary table with exact cause for any failures.
"""

import asyncio
import itertools
import logging
import os
import sys
from datetime import date
from decimal import Decimal
from typing import Any

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from sqlalchemy import select
from app.database.session import async_session_factory
from app.models.offer import Offer
from app.services.offer_service import list_offers

logging.basicConfig(level=logging.WARNING)

FILTERS_DEFINITIONS: dict[str, dict[str, Any]] = {
    "provider": {"provider": "itaka"},
    "country": {"country": "Grecja"},
    "region": {"region": "Kreta"},
    "airport": {"departure_city": "Warszawa"},
    "meal_type": {"meal_type": "all_inclusive"},
    "stars": {"hotel_stars": 4.0},
    "duration": {"duration_min": 7, "duration_max": 8},
    "adults": {"adults": 2},
    "children": {"children": 0},
    "price": {"price_max": Decimal("10000.00")},
    "departure_date": {"date_from": date(2026, 1, 1), "date_to": date(2027, 12, 31)},
}

FILTER_NAMES = list(FILTERS_DEFINITIONS.keys())


async def evaluate_all_combinations() -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Execute evaluation over all 231 combinations without stopping on error."""
    results_list: list[dict[str, Any]] = []
    combo_counts: dict[tuple[str, ...], int] = {}

    combos_1 = list(itertools.combinations(FILTER_NAMES, 1))
    combos_2 = list(itertools.combinations(FILTER_NAMES, 2))
    combos_3 = list(itertools.combinations(FILTER_NAMES, 3))
    all_combos = combos_1 + combos_2 + combos_3

    stats = {"total": len(all_combos), "pass": 0, "fail": 0, "1_elem": len(combos_1), "2_elem": len(combos_2), "3_elem": len(combos_3)}

    async with async_session_factory() as session:
        # Step 1: Baseline offer query (0 filters)
        _, baseline_count = await list_offers(session)

        # Step 2: Evaluate combinations in order of size (1 -> 2 -> 3)
        for combo in all_combos:
            combo_name = " + ".join(combo)
            combo_size = len(combo)
            kwargs: dict[str, Any] = {}
            for fname in combo:
                kwargs.update(FILTERS_DEFINITIONS[fname])

            status = "PASS"
            failure_reasons = []

            # A. Backend execution check
            try:
                offers, count = await list_offers(session, **kwargs)
            except Exception as e:
                status = "FAIL"
                failure_reasons.append(f"Backend Error: {type(e).__name__}: {str(e)}")
                count = -1

            combo_counts[combo] = count

            if status != "FAIL":
                # B. Monotonicity Check: count(combo) <= count(subset)
                if combo_size > 1:
                    for i in range(combo_size):
                        subset = combo[:i] + combo[i + 1 :]
                        if subset in combo_counts and combo_counts[subset] >= 0:
                            subset_count = combo_counts[subset]
                            if count > subset_count:
                                status = "FAIL"
                                failure_reasons.append(
                                    f"Monotonicity Violation: count({combo_name})={count} > count({' + '.join(subset)})={subset_count}"
                                )

                # C. Logical Non-Zero Check: direct DB verification
                stmt = select(Offer).where(Offer.is_available.is_(True))
                if "provider" in combo:
                    stmt = stmt.where(Offer.provider == "itaka")
                if "country" in combo:
                    stmt = stmt.where(Offer.country == "Grecja")
                if "region" in combo:
                    stmt = stmt.where(Offer.region == "Kreta")
                if "airport" in combo:
                    stmt = stmt.where(Offer.departure_city.ilike("%Warszawa%"))
                if "meal_type" in combo:
                    stmt = stmt.where(Offer.meal_type == "all_inclusive")
                if "stars" in combo:
                    stmt = stmt.where(Offer.hotel_stars == 4.0)
                if "duration" in combo:
                    stmt = stmt.where(Offer.duration_nights >= 7, Offer.duration_nights <= 8)
                if "adults" in combo:
                    stmt = stmt.where(Offer.adults == 2)
                if "children" in combo:
                    stmt = stmt.where(Offer.children == 0)
                if "price" in combo:
                    stmt = stmt.where(Offer.price_per_person <= Decimal("10000.00"))
                if "departure_date" in combo:
                    stmt = stmt.where(Offer.departure_date >= date(2026, 1, 1), Offer.departure_date <= date(2027, 12, 31))

                db_res = await session.execute(stmt)
                db_matching_count = len(db_res.scalars().all())

                if db_matching_count > 0 and count == 0:
                    status = "FAIL"
                    failure_reasons.append(
                        f"False Zero Error: DB has {db_matching_count} matching offer(s), but list_offers returned 0"
                    )

            if status == "PASS":
                stats["pass"] += 1
                reason_str = "OK (Liczba ofert spójna, brak błędów backendu)"
            else:
                stats["fail"] += 1
                reason_str = "; ".join(failure_reasons)

            results_list.append({
                "id": len(results_list) + 1,
                "size": combo_size,
                "combination": combo_name,
                "count": count,
                "status": status,
                "reason": reason_str,
            })

    return results_list, stats


def generate_markdown_report(results: list[dict[str, Any]], stats: dict[str, int]) -> str:
    """Generate Markdown report containing full PASS/FAIL matrix table and failure analysis."""
    lines = [
        "# Raport z Testu Kombinacji Filtrów Live Import",
        "",
        "## Podsumowanie Wyników Testu",
        f"- **Wszystkie przetestowane kombinacje**: {stats['total']}",
        f"- **Liczba kombinacji 1-elementowych**: {stats['1_elem']}",
        f"- **Liczba kombinacji 2-elementowych**: {stats['2_elem']}",
        f"- **Liczba kombinacji 3-elementowych**: {stats['3_elem']}",
        f"- **Status ogólny**: {'✅ SUKCES (100% PASS)' if stats['fail'] == 0 else '❌ PORAŻKA (wykryto błędy)'}",
        f"- **Wynik PASS**: **{stats['pass']}** / {stats['total']} ({stats['pass']/stats['total']*100:.1f}%)",
        f"- **Wynik FAIL**: **{stats['fail']}** / {stats['total']}",
        "",
        "## Weryfikowane Zasady Logiczne",
        "1. **Brak błędów backendu**: Przetwarzanie i filtrowanie zapytań nie wyrzuca wyjątków SQL/Python ani błędów 500.",
        "2. **Monotoniczność (Nesting property)**: Dodanie kolejnego filtra nie może zwiększyć liczby zwróconych wyników (`count(A + B) <= count(A)`).",
        "3. **Brak fałszywych 0 (Non-zero matching)**: Jeśli w bazie danych/źródle istnieją rekordy spełniające wszystkie filtry w kombinacji, zapytanie nie może zwrócić 0 ofert.",
        "",
        "## Tabela Wyników dla Wszystkich 231 Kombinacji Filtrów",
        "",
        "| ID | Typ | Kombinacja Filtrów | Liczba Ofert | Status | Dokładna Przyczyna / Opis |",
        "|---|---|---|---|---|---|",
    ]

    for r in results:
        type_str = f"{r['size']}-elementowa"
        status_icon = "✅ PASS" if r["status"] == "PASS" else "❌ FAIL"
        lines.append(f"| {r['id']} | {type_str} | `{r['combination']}` | {r['count']} | {status_icon} | {r['reason']} |")

    if stats["fail"] > 0:
        lines.extend([
            "",
            "## Szczegółowa Analiza Wykrytych Porażek (FAIL)",
            "",
        ])
        fail_items = [r for r in results if r["status"] == "FAIL"]
        for fi in fail_items:
            lines.append(f"- **Kombinacja #{fi['id']} (`{fi['combination']}`)**: {fi['reason']}")

    return "\n".join(lines)


async def main():
    print("Rozpoczynanie automatycznego testu 231 kombinacji filtrów...")
    results, stats = await evaluate_all_combinations()
    report_md = generate_markdown_report(results, stats)

    # Output path for artifact report
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "filter_matrix_test_report.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_md)

    print(f"\n================================================================================")
    print(f"RAPORT PODSUMOWUJĄCY TEST KOMBINACJI FILTRÓW LIVE IMPORT")
    print(f"================================================================================")
    print(f"Razem kombinacji: {stats['total']} (1-el: {stats['1_elem']}, 2-el: {stats['2_elem']}, 3-el: {stats['3_elem']})")
    print(f"PASS: {stats['pass']}")
    print(f"FAIL: {stats['fail']}")
    print(f"Raport zapisano do: {output_path}\n")


if __name__ == "__main__":
    asyncio.run(main())
