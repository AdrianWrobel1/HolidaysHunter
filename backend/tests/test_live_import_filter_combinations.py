"""Pytest suite for all live import filter combinations (1-, 2-, and 3-element)."""

import asyncio
import itertools
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import select

from app.models.offer import Offer
from app.services.offer_service import list_offers

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

# Generate all 231 combinations
COMBOS_1 = list(itertools.combinations(FILTER_NAMES, 1))
COMBOS_2 = list(itertools.combinations(FILTER_NAMES, 2))
COMBOS_3 = list(itertools.combinations(FILTER_NAMES, 3))
ALL_COMBINATIONS = COMBOS_1 + COMBOS_2 + COMBOS_3


@pytest.mark.asyncio
async def test_all_231_filter_combinations(db_session):
    """Execute evaluation over all 231 filter combinations.

    Verifies:
    1. No backend exceptions or errors.
    2. Monotonicity constraint: count(A+B) <= count(A).
    3. Logical consistency: No false zeros when matching records exist in database.
    """
    combo_counts: dict[tuple[str, ...], int] = {}
    failures: list[str] = []

    for combo in ALL_COMBINATIONS:
        combo_name = " + ".join(combo)
        kwargs: dict[str, Any] = {}
        for fname in combo:
            kwargs.update(FILTERS_DEFINITIONS[fname])

        try:
            offers, count = await list_offers(db_session, **kwargs)
        except Exception as e:
            failures.append(f"❌ {combo_name}: Backend Error ({type(e).__name__}: {e})")
            continue

        combo_counts[combo] = count

        # Check monotonicity against subsets
        if len(combo) > 1:
            for i in range(len(combo)):
                subset = combo[:i] + combo[i + 1 :]
                if subset in combo_counts and combo_counts[subset] >= 0:
                    subset_count = combo_counts[subset]
                    if count > subset_count:
                        failures.append(
                            f"❌ {combo_name}: Monotonicity Violation (count={count} > subset count={subset_count})"
                        )

        # Check non-zero consistency against direct DB query
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

        db_res = await db_session.execute(stmt)
        db_matching_count = len(db_res.scalars().all())

        if db_matching_count > 0 and count == 0:
            failures.append(
                f"❌ {combo_name}: False Zero Error (DB has {db_matching_count} matching records, query returned 0)"
            )

    assert not failures, f"Failed {len(failures)} out of {len(ALL_COMBINATIONS)} filter combinations:\n" + "\n".join(failures)
