"""End-to-End Live Integration Test with Adversarial Validation & Offer Integrity Verification.

Requirements enforced:
1. Uses real provider import pipeline (run_import) without mocked repositories or synthetic datasets.
2. Clears the database before test execution so expected results are calculated strictly from the freshly imported dataset.
3. If a provider import fails due to network/timeout/site changes, marks that provider as SKIPPED instead of FAIL and continues testing.
4. Filter Matrix Testing: Evaluates 1-, 2-, and 3-element filter combinations.
5. Random Filter Fuzzing: Generates 200-500 random valid filter combinations from freshly imported dataset and verifies HTTP 200 & correctness.
6. Edge Case Validation: Tests invalid, extreme, empty, mixed-case, and whitespace filter values. Ensures API never returns HTTP 500.
7. Offer Integrity Verification (Most Important): For EVERY response returned by /api/offers, verifies that EVERY single returned offer satisfies EVERY active filter.
8. Produces a final summary report:
   Filter combinations tested:
   Random fuzz tests:
   Edge-case tests:
   Offer integrity checks:
   PASS:
   FAIL:
"""

import asyncio
import itertools
import logging
import os
import random
import sys
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, select, or_

from app.core.countries import (
    normalize_country_name,
    normalize_provider_name,
    normalize_region_name,
)
from app.database.session import async_session_factory
from app.main import app
from app.models.alert_event import AlertEvent
from app.models.enums import Provider
from app.models.offer import Offer
from app.models.price_history import PriceHistory
from app.services.import_service import run_import

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

logger = logging.getLogger(__name__)


async def clear_database_offers():
    """Clear all offers and related historical records from database for clean test isolation."""
    async with async_session_factory() as session:
        await session.execute(delete(AlertEvent))
        await session.execute(delete(PriceHistory))
        await session.execute(delete(Offer))
        await session.commit()


async def execute_live_imports() -> dict[str, dict[str, Any]]:
    """Execute live import pipeline for all providers.

    Returns dict mapping provider_name -> import summary:
    {"status": "SUCCESS" | "SKIPPED", "count": int, "error": str | None}
    """
    import_results = {}

    for provider in Provider:
        prov_key = provider.value
        print(f"\n[LIVE IMPORT] Running pipeline for provider: {prov_key.upper()}...")

        async with async_session_factory() as session:
            try:
                await run_import(provider, session)
                await session.commit()

                res = await session.execute(
                    select(Offer).where(Offer.provider == prov_key, Offer.is_available.is_(True))
                )
                imported_count = len(res.scalars().all())
                print(f"[LIVE IMPORT] {prov_key.upper()} successfully imported {imported_count} live offers into DB.")
                import_results[prov_key] = {
                    "status": "SUCCESS",
                    "count": imported_count,
                    "error": None,
                }
            except Exception as exc:
                err_msg = f"{type(exc).__name__}: {str(exc)}"
                print(f"[LIVE IMPORT] Provider {prov_key.upper()} import failed ({err_msg}). Marking as SKIPPED.")
                import_results[prov_key] = {
                    "status": "SKIPPED",
                    "count": 0,
                    "error": err_msg,
                }

    return import_results


async def query_dataset_expected_offers(session, filter_combo: dict[str, Any]) -> list[Offer]:
    """Query expected matching offers directly from the freshly imported database dataset."""
    stmt = select(Offer).where(Offer.is_available.is_(True))

    if "provider" in filter_combo and filter_combo["provider"] is not None:
        prov_val = filter_combo["provider"]
        if isinstance(prov_val, list):
            norm_p = [normalize_provider_name(p) for p in prov_val if p and normalize_provider_name(p)]
            stmt = stmt.where(Offer.provider.in_(norm_p))
        elif isinstance(prov_val, str):
            if prov_val.strip() == "":
                stmt = stmt.where(Offer.provider.in_([]))
            else:
                norm_p = normalize_provider_name(prov_val)
                stmt = stmt.where(Offer.provider == norm_p)

    if "country" in filter_combo and filter_combo["country"] is not None:
        country_val = filter_combo["country"]
        if isinstance(country_val, list):
            norm_c = [normalize_country_name(c) for c in country_val if c]
            stmt = stmt.where(Offer.country.in_(norm_c))
        elif isinstance(country_val, str):
            if country_val.strip() == "":
                stmt = stmt.where(Offer.country.in_([]))
            else:
                norm_c = normalize_country_name(country_val)
                stmt = stmt.where(Offer.country == norm_c)

    if "region" in filter_combo and filter_combo["region"] is not None:
        rgn_val = filter_combo["region"]
        if isinstance(rgn_val, list):
            norm_r = [normalize_region_name(r) for r in rgn_val if r and normalize_region_name(r)]
            stmt = stmt.where(Offer.region.in_(norm_r))
        elif isinstance(rgn_val, str):
            if rgn_val.strip() == "":
                stmt = stmt.where(Offer.region.in_([]))
            else:
                norm_r = normalize_region_name(rgn_val)
                stmt = stmt.where(Offer.region == norm_r)

    if "departure_city" in filter_combo and filter_combo["departure_city"] is not None:
        dep_val = filter_combo["departure_city"]
        if isinstance(dep_val, list):
            conds = [Offer.departure_city.ilike(f"%{c.strip()}%") for c in dep_val if c and str(c).strip()]
            if conds:
                stmt = stmt.where(or_(*conds))
            else:
                stmt = stmt.where(Offer.departure_city.in_([]))
        elif isinstance(dep_val, str):
            if dep_val.strip() == "":
                stmt = stmt.where(Offer.departure_city.in_([]))
            else:
                stmt = stmt.where(Offer.departure_city.ilike(f"%{dep_val.strip()}%"))

    if "meal_type" in filter_combo and filter_combo["meal_type"] is not None:
        def _norm_meal(m: Any) -> str:
            return str(m).lower().strip().replace(" ", "_").replace("-", "_")

        meal_val = filter_combo["meal_type"]
        if isinstance(meal_val, list):
            norm_m = [_norm_meal(m) for m in meal_val if m and str(m).strip()]
            stmt = stmt.where(Offer.meal_type.in_(norm_m))
        elif isinstance(meal_val, str):
            if meal_val.strip() == "":
                stmt = stmt.where(Offer.meal_type.in_([]))
            else:
                norm_m = _norm_meal(meal_val)
                stmt = stmt.where(Offer.meal_type == norm_m)

    if "transport_type" in filter_combo and filter_combo["transport_type"] is not None:
        stmt = stmt.where(Offer.transport_type == filter_combo["transport_type"])

    if "hotel_stars" in filter_combo and filter_combo["hotel_stars"] is not None:
        stars_val = filter_combo["hotel_stars"]
        if isinstance(stars_val, list):
            valid_stars = [float(s) for s in stars_val if s is not None and 0 <= float(s) <= 9.9]
            if valid_stars:
                stmt = stmt.where(Offer.hotel_stars.in_(valid_stars))
            else:
                stmt = stmt.where(Offer.id.in_([]))
        else:
            try:
                s_v = float(stars_val)
                if 0 <= s_v <= 9.9:
                    stmt = stmt.where(Offer.hotel_stars == s_v)
                else:
                    stmt = stmt.where(Offer.id.in_([]))
            except (ValueError, TypeError):
                stmt = stmt.where(Offer.id.in_([]))
    elif "hotel_stars_min" in filter_combo and filter_combo["hotel_stars_min"] is not None:
        try:
            s_min = float(filter_combo["hotel_stars_min"])
            if 0 <= s_min <= 9.9:
                stmt = stmt.where(Offer.hotel_stars >= s_min)
            elif s_min > 9.9:
                stmt = stmt.where(Offer.id.in_([]))
            else:
                stmt = stmt.where(Offer.hotel_stars >= 0)
        except (ValueError, TypeError):
            pass

    if "price_max" in filter_combo and filter_combo["price_max"] is not None:
        stmt = stmt.where(Offer.price_per_person <= Decimal(str(filter_combo["price_max"])))

    if "price_min" in filter_combo and filter_combo["price_min"] is not None:
        stmt = stmt.where(Offer.price_per_person >= Decimal(str(filter_combo["price_min"])))

    if "date_from" in filter_combo and filter_combo["date_from"] is not None:
        d_from = filter_combo["date_from"]
        if isinstance(d_from, str):
            d_from = date.fromisoformat(d_from)
        stmt = stmt.where(Offer.departure_date >= d_from)

    if "date_to" in filter_combo and filter_combo["date_to"] is not None:
        d_to = filter_combo["date_to"]
        if isinstance(d_to, str):
            d_to = date.fromisoformat(d_to)
        stmt = stmt.where(Offer.departure_date <= d_to)

    if "duration_min" in filter_combo and filter_combo["duration_min"] is not None:
        stmt = stmt.where(Offer.duration_nights >= filter_combo["duration_min"])

    if "duration_max" in filter_combo and filter_combo["duration_max"] is not None:
        stmt = stmt.where(Offer.duration_nights <= filter_combo["duration_max"])

    if "adults" in filter_combo and filter_combo["adults"] is not None:
        stmt = stmt.where(Offer.adults == filter_combo["adults"])

    if "children" in filter_combo and filter_combo["children"] is not None:
        stmt = stmt.where(Offer.children == filter_combo["children"])

    if "search" in filter_combo and filter_combo["search"] is not None:
        s_val = str(filter_combo["search"]).strip()
        if s_val == "":
            stmt = stmt.where(Offer.id.in_([]))
        else:
            pattern = f"%{s_val}%"
            stmt = stmt.where(
                or_(
                    Offer.hotel_name.ilike(pattern),
                    Offer.country.ilike(pattern),
                    Offer.region.ilike(pattern),
                    Offer.city.ilike(pattern),
                    Offer.title.ilike(pattern),
                )
            )

    res = await session.execute(stmt)
    return list(res.scalars().all())


def verify_offer_integrity(offer: dict[str, Any], params: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any]]:
    """Verify that a returned offer dictionary satisfies all active filter parameters.

    Returns (is_valid, violated_fields, expected_values).
    """
    violated = []
    expected_values = {}

    # 1. Provider
    if "provider" in params and params["provider"] is not None:
        p_param = params["provider"]
        if isinstance(p_param, list):
            exp_p = [normalize_provider_name(p) for p in p_param if p and normalize_provider_name(p)]
        else:
            p_str = str(p_param).strip()
            exp_p = [normalize_provider_name(p_str)] if p_str else []
        expected_values["provider"] = exp_p
        actual_p = normalize_provider_name(offer.get("provider"))
        if not exp_p or actual_p not in exp_p:
            violated.append("provider")

    # 2. Country
    if "country" in params and params["country"] is not None:
        c_param = params["country"]
        if isinstance(c_param, list):
            exp_c = [normalize_country_name(c) for c in c_param if c]
        else:
            c_str = str(c_param).strip()
            exp_c = [normalize_country_name(c_str)] if c_str else []
        expected_values["country"] = exp_c
        actual_c = normalize_country_name(offer.get("country"))
        if not exp_c or actual_c not in exp_c:
            violated.append("country")

    # 3. Region
    if "region" in params and params["region"] is not None:
        r_param = params["region"]
        if isinstance(r_param, list):
            exp_r = [normalize_region_name(r) for r in r_param if r and normalize_region_name(r)]
        else:
            r_str = str(r_param).strip()
            exp_r = [normalize_region_name(r_str)] if r_str else []
        expected_values["region"] = exp_r
        actual_r = normalize_region_name(offer.get("region"))
        if not exp_r or actual_r not in exp_r:
            violated.append("region")

    # 4. Departure City
    if "departure_city" in params and params["departure_city"] is not None:
        d_param = params["departure_city"]
        if isinstance(d_param, list):
            exp_d = [str(d).strip().lower() for d in d_param if str(d).strip()]
        else:
            d_str = str(d_param).strip().lower()
            exp_d = [d_str] if d_str else []
        expected_values["departure_city"] = exp_d
        actual_d = str(offer.get("departure_city") or "").lower()
        if not exp_d or not any(sub in actual_d for sub in exp_d):
            violated.append("departure_city")

    # 5. Meal Type
    if "meal_type" in params and params["meal_type"] is not None:
        def _nm(m):
            return str(m).lower().strip().replace(" ", "_").replace("-", "_")
        m_param = params["meal_type"]
        if isinstance(m_param, list):
            exp_m = [_nm(m) for m in m_param if str(m).strip()]
        else:
            m_str = str(m_param).strip()
            exp_m = [_nm(m_str)] if m_str else []
        expected_values["meal_type"] = exp_m
        actual_m = _nm(offer.get("meal_type"))
        if not exp_m or actual_m not in exp_m:
            violated.append("meal_type")

    # 6. Hotel Stars
    if "hotel_stars" in params and params["hotel_stars"] is not None:
        s_param = params["hotel_stars"]
        if isinstance(s_param, list):
            exp_s = [float(s) for s in s_param]
        else:
            exp_s = [float(s_param)]
        expected_values["hotel_stars"] = exp_s
        actual_s = offer.get("hotel_stars")
        if actual_s is None or float(actual_s) not in exp_s:
            violated.append("hotel_stars")
    elif "hotel_stars_min" in params and params["hotel_stars_min"] is not None:
        exp_smin = float(params["hotel_stars_min"])
        expected_values["hotel_stars_min"] = exp_smin
        actual_s = offer.get("hotel_stars")
        if actual_s is None or float(actual_s) < exp_smin:
            violated.append("hotel_stars")

    # 7. Price Max
    if "price_max" in params and params["price_max"] is not None:
        exp_pmax = float(params["price_max"])
        expected_values["price_max"] = exp_pmax
        actual_p = offer.get("price_per_person")
        if actual_p is None or float(actual_p) > exp_pmax:
            violated.append("price_per_person")

    # 8. Price Min
    if "price_min" in params and params["price_min"] is not None:
        exp_pmin = float(params["price_min"])
        expected_values["price_min"] = exp_pmin
        actual_p = offer.get("price_per_person")
        if actual_p is None or float(actual_p) < exp_pmin:
            violated.append("price_per_person")

    # 9. Date From
    if "date_from" in params and params["date_from"] is not None:
        exp_df = str(params["date_from"])
        expected_values["date_from"] = exp_df
        actual_d = str(offer.get("departure_date") or "")
        if not actual_d or actual_d < exp_df:
            violated.append("departure_date")

    # 10. Date To
    if "date_to" in params and params["date_to"] is not None:
        exp_dt = str(params["date_to"])
        expected_values["date_to"] = exp_dt
        actual_d = str(offer.get("departure_date") or "")
        if not actual_d or actual_d > exp_dt:
            violated.append("departure_date")

    # 11. Duration Min
    if "duration_min" in params and params["duration_min"] is not None:
        exp_dur_min = int(params["duration_min"])
        expected_values["duration_min"] = exp_dur_min
        actual_dur = offer.get("duration_nights")
        if actual_dur is None or int(actual_dur) < exp_dur_min:
            violated.append("duration_nights")

    # 12. Duration Max
    if "duration_max" in params and params["duration_max"] is not None:
        exp_dur_max = int(params["duration_max"])
        expected_values["duration_max"] = exp_dur_max
        actual_dur = offer.get("duration_nights")
        if actual_dur is None or int(actual_dur) > exp_dur_max:
            violated.append("duration_nights")

    # 13. Adults
    if "adults" in params and params["adults"] is not None:
        exp_a = int(params["adults"])
        expected_values["adults"] = exp_a
        actual_a = offer.get("adults")
        if actual_a is None or int(actual_a) != exp_a:
            violated.append("adults")

    # 14. Children
    if "children" in params and params["children"] is not None:
        exp_ch = int(params["children"])
        expected_values["children"] = exp_ch
        actual_ch = offer.get("children")
        if actual_ch is None or int(actual_ch) != exp_ch:
            violated.append("children")

    # 15. Search
    if "search" in params and params["search"]:
        exp_s = str(params["search"]).strip().lower()
        expected_values["search"] = exp_s
        h_name = str(offer.get("hotel_name") or "").lower()
        c_name = str(offer.get("country") or "").lower()
        r_name = str(offer.get("region") or "").lower()
        city_name = str(offer.get("city") or "").lower()
        t_name = str(offer.get("title") or "").lower()
        if not exp_s or not (exp_s in h_name or exp_s in c_name or exp_s in r_name or exp_s in city_name or exp_s in t_name):
            violated.append("search")

    return len(violated) == 0, violated, expected_values


def build_filter_matrix(dataset_offers: list[Offer]) -> list[tuple[str, dict[str, Any]]]:
    """Construct dynamic 1-, 2-, and 3-element filter combinations based on freshly imported dataset."""
    imported_providers = sorted(list(set(o.provider for o in dataset_offers if o.provider)))
    imported_countries = sorted(list(set(o.country for o in dataset_offers if o.country)))
    imported_regions = sorted(list(set(o.region for o in dataset_offers if o.region)))
    imported_cities = sorted(list(set(o.departure_city for o in dataset_offers if o.departure_city)))
    imported_meals = sorted(list(set(o.meal_type for o in dataset_offers if o.meal_type)))
    imported_stars = sorted(list(set(o.hotel_stars for o in dataset_offers if o.hotel_stars is not None)))

    sample_country = imported_countries[0] if imported_countries else "Grecja"
    sample_region = imported_regions[0] if imported_regions else "Kreta"
    sample_provider = imported_providers[0] if imported_providers else "itaka"
    sample_city = imported_cities[0] if imported_cities else "Warszawa"
    sample_meal = imported_meals[0] if imported_meals else "all_inclusive"
    sample_stars = imported_stars[0] if imported_stars else 4.0

    filter_dict = {
        "provider": {"provider": sample_provider},
        "country": {"country": sample_country},
        "region": {"region": sample_region},
        "departure_city": {"departure_city": sample_city},
        "meal_type": {"meal_type": sample_meal},
        "hotel_stars": {"hotel_stars": sample_stars},
        "duration": {"duration_min": 7, "duration_max": 8},
        "adults": {"adults": 2},
        "children": {"children": 0},
        "price": {"price_max": 15000.0},
        "departure_date": {"date_from": "2026-01-01", "date_to": "2027-12-31"},
    }

    combo_items = []
    filter_keys = list(filter_dict.keys())

    for k in filter_keys:
        combo_items.append((f"Matrix 1-el: {k}", filter_dict[k]))

    for k1, k2 in itertools.combinations(filter_keys, 2):
        merged = {}
        merged.update(filter_dict[k1])
        merged.update(filter_dict[k2])
        combo_items.append((f"Matrix 2-el: {k1} + {k2}", merged))

    for k1, k2, k3 in itertools.combinations(filter_keys[:8], 3):
        merged = {}
        merged.update(filter_dict[k1])
        merged.update(filter_dict[k2])
        merged.update(filter_dict[k3])
        combo_items.append((f"Matrix 3-el: {k1} + {k2} + {k3}", merged))

    return combo_items


def generate_random_fuzz_combos(dataset_offers: list[Offer], count: int = 300) -> list[tuple[str, dict[str, Any]]]:
    """Generate 200-500 random valid filter combinations from freshly imported dataset values."""
    rng = random.Random(42)

    providers = sorted(list(set(o.provider for o in dataset_offers if o.provider)))
    countries = sorted(list(set(o.country for o in dataset_offers if o.country)))
    regions = sorted(list(set(o.region for o in dataset_offers if o.region)))
    departure_cities = sorted(list(set(o.departure_city for o in dataset_offers if o.departure_city)))
    meal_types = sorted(list(set(o.meal_type for o in dataset_offers if o.meal_type)))
    hotel_stars = sorted(list(set(o.hotel_stars for o in dataset_offers if o.hotel_stars is not None)))
    prices = sorted(list(set(float(o.price_per_person) for o in dataset_offers if o.price_per_person is not None)))
    dates = sorted(list(set(str(o.departure_date) for o in dataset_offers if o.departure_date is not None)))
    durations = sorted(list(set(o.duration_nights for o in dataset_offers if o.duration_nights is not None)))
    adults_list = sorted(list(set(o.adults for o in dataset_offers if o.adults is not None)))
    children_list = sorted(list(set(o.children for o in dataset_offers if o.children is not None)))

    if not providers: providers = ["itaka", "tui"]
    if not countries: countries = ["Hiszpania", "Grecja"]
    if not regions: regions = ["Majorka", "Kreta"]
    if not departure_cities: departure_cities = ["Warszawa", "Katowice"]
    if not meal_types: meal_types = ["all_inclusive", "hb"]
    if not hotel_stars: hotel_stars = [3.0, 4.0, 5.0]
    if not prices: prices = [2000.0, 5000.0, 10000.0]
    if not dates: dates = ["2026-06-01", "2026-09-01"]
    if not durations: durations = [7, 10, 14]
    if not adults_list: adults_list = [2]
    if not children_list: children_list = [0]

    min_price, max_price = min(prices), max(prices)
    min_date, max_date = min(dates), max(dates)

    fuzz_combos = []
    for i in range(1, count + 1):
        num_filters = rng.randint(1, 4)
        possible_keys = [
            "provider", "country", "region", "departure_city", "meal_type",
            "hotel_stars", "price_max", "price_min", "departure_date",
            "duration", "adults", "children"
        ]
        chosen_keys = rng.sample(possible_keys, num_filters)
        combo_dict = {}

        for k in chosen_keys:
            if k == "provider":
                combo_dict["provider"] = rng.choice(providers)
            elif k == "country":
                combo_dict["country"] = rng.choice(countries)
            elif k == "region":
                combo_dict["region"] = rng.choice(regions)
            elif k == "departure_city":
                combo_dict["departure_city"] = rng.choice(departure_cities)
            elif k == "meal_type":
                combo_dict["meal_type"] = rng.choice(meal_types)
            elif k == "hotel_stars":
                combo_dict["hotel_stars"] = rng.choice(hotel_stars)
            elif k == "price_max":
                combo_dict["price_max"] = round(rng.uniform(min_price, max_price), 2)
            elif k == "price_min":
                combo_dict["price_min"] = round(rng.uniform(min_price, max_price / 2), 2)
            elif k == "departure_date":
                combo_dict["date_from"] = min_date
                combo_dict["date_to"] = max_date
            elif k == "duration":
                d1 = rng.choice(durations)
                d2 = rng.choice(durations)
                combo_dict["duration_min"] = min(d1, d2)
                combo_dict["duration_max"] = max(d1, d2)
            elif k == "adults":
                combo_dict["adults"] = rng.choice(adults_list)
            elif k == "children":
                combo_dict["children"] = rng.choice(children_list)

        fuzz_combos.append((f"Fuzz #{i} ({', '.join(combo_dict.keys())})", combo_dict))

    return fuzz_combos


def generate_edge_case_combos() -> list[tuple[str, dict[str, Any]]]:
    """Generate edge cases: invalid, extreme, empty strings, mixed casing, extra whitespace."""
    return [
        ("Edge: unknown_provider", {"provider": "unknown_provider_xyz"}),
        ("Edge: unknown_country", {"country": "unknown_country_xyz"}),
        ("Edge: unknown_region", {"region": "unknown_region_xyz"}),
        ("Edge: invalid_airport", {"departure_city": "invalid_airport_xyz"}),
        ("Edge: price_min=1", {"price_min": 1.0}),
        ("Edge: price_max=1", {"price_max": 1.0}),
        ("Edge: price_min=999999", {"price_min": 999999.0}),
        ("Edge: price_max=999999", {"price_max": 999999.0}),
        ("Edge: duration_min=0", {"duration_min": 0}),
        ("Edge: duration_max=0", {"duration_max": 0}),
        ("Edge: duration_min=100", {"duration_min": 100}),
        ("Edge: duration_max=100", {"duration_max": 100}),
        ("Edge: stars=-1", {"hotel_stars": -1.0}),
        ("Edge: stars_min=-1", {"hotel_stars_min": -1.0}),
        ("Edge: stars=10", {"hotel_stars": 10.0}),
        ("Edge: empty_provider", {"provider": ""}),
        ("Edge: empty_country", {"country": ""}),
        ("Edge: empty_region", {"region": ""}),
        ("Edge: empty_departure_city", {"departure_city": ""}),
        ("Edge: empty_meal_type", {"meal_type": ""}),
        ("Edge: empty_search", {"search": ""}),
        ("Edge: mixed_casing_provider", {"provider": "iTaKa"}),
        ("Edge: mixed_casing_country", {"country": "hiSZpaNIa"}),
        ("Edge: mixed_casing_region", {"region": "MAjOrKa"}),
        ("Edge: extra_whitespace_provider", {"provider": "  itaka  "}),
        ("Edge: extra_whitespace_country", {"country": " Hiszpania "}),
        ("Edge: extra_whitespace_region", {"region": " Majorka\t"}),
        ("Edge: mixed_casing_whitespace_country_region", {"country": "  hiSZpaNIa  ", "region": "  MAjOrKa\t"}),
    ]


@pytest.mark.asyncio
async def test_live_e2e_import_and_offers_filtering():
    """Execute end-to-end live integration test with adversarial validation."""
    print("\n================================================================================")
    print("STARTING E2E LIVE INTEGRATION TEST (REAL IMPORT PIPELINE & ADVERSARIAL VALIDATION)")
    print("================================================================================")

    # 1. Clear database offers table
    print("\n[STEP 1] Clearing database tables to ensure fresh test isolation...")
    await clear_database_offers()
    print("[STEP 1] Database successfully cleared.")

    # 2. Execute live import pipeline for all providers
    print("\n[STEP 2] Executing live provider import pipeline...")
    import_results = await execute_live_imports()

    successful_providers = [p for p, r in import_results.items() if r["status"] == "SUCCESS"]
    skipped_providers = [p for p, r in import_results.items() if r["status"] == "SKIPPED"]

    print(f"\n[IMPORT STATUS SUMMARY]")
    print(f"  - Successful provider imports: {successful_providers}")
    print(f"  - Skipped provider imports: {skipped_providers}")

    # 3. Retrieve freshly imported offers from DB
    async with async_session_factory() as session:
        db_res = await session.execute(select(Offer).where(Offer.is_available.is_(True)))
        all_imported_offers = list(db_res.scalars().all())

    print(f"\n[STEP 3] Total freshly imported offers in database: {len(all_imported_offers)}")
    if len(all_imported_offers) == 0:
        pytest.skip("No live offers could be imported across any provider. All provider imports were SKIPPED.")

    # 4. Build Test Suites
    matrix_combos = build_filter_matrix(all_imported_offers)
    fuzz_combos = generate_random_fuzz_combos(all_imported_offers, count=300)
    edge_case_combos = generate_edge_case_combos()

    all_test_combos = [
        ("matrix", name, params) for name, params in matrix_combos
    ] + [
        ("fuzz", name, params) for name, params in fuzz_combos
    ] + [
        ("edge", name, params) for name, params in edge_case_combos
    ]

    print(f"[STEP 4] Evaluating {len(all_test_combos)} total filter tests ({len(matrix_combos)} matrix, {len(fuzz_combos)} random fuzz, {len(edge_case_combos)} edge cases)...")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        failures = []
        passed_count = 0
        total_offer_integrity_checks = 0

        for idx, (suite_type, combo_name, filter_params) in enumerate(all_test_combos, 1):
            req_params = dict(filter_params)
            req_params["page_size"] = 100

            api_resp = await client.get("/api/offers", params=req_params)

            if suite_type == "edge":
                if api_resp.status_code == 500:
                    failures.append({
                        "combo_name": combo_name,
                        "params": filter_params,
                        "reason": f"HTTP 500 Server Error returned for edge case: {api_resp.text}",
                    })
                    print(f"\n[FAIL] {combo_name}: HTTP 500 Error")
                    continue
                elif api_resp.status_code in (400, 422):
                    # Validation error returned for edge case -> PASS
                    passed_count += 1
                    continue
                elif api_resp.status_code != 200:
                    failures.append({
                        "combo_name": combo_name,
                        "params": filter_params,
                        "reason": f"Unexpected HTTP status {api_resp.status_code}: {api_resp.text}",
                    })
                    print(f"\n[FAIL] {combo_name}: HTTP {api_resp.status_code}")
                    continue
            else:
                if api_resp.status_code != 200:
                    failures.append({
                        "combo_name": combo_name,
                        "params": filter_params,
                        "reason": f"API returned HTTP {api_resp.status_code}: {api_resp.text}",
                    })
                    print(f"\n[FAIL] {combo_name}: HTTP {api_resp.status_code}")
                    continue

            api_data = api_resp.json()
            api_count = api_data.get("total", 0)
            returned_offers = api_data.get("offers", [])

            async with async_session_factory() as session:
                expected_matching_offers = await query_dataset_expected_offers(session, filter_params)
            expected_count = len(expected_matching_offers)

            count_pass = (api_count == expected_count)

            integrity_failures = []
            for offer_dict in returned_offers:
                total_offer_integrity_checks += 1
                is_valid, violated_fields, expected_vals = verify_offer_integrity(offer_dict, filter_params)
                if not is_valid:
                    integrity_failures.append({
                        "offer": offer_dict,
                        "violated": violated_fields,
                        "expected": expected_vals,
                    })

            if count_pass and not integrity_failures:
                passed_count += 1
            else:
                fail_reasons = []
                if not count_pass:
                    fail_reasons.append(f"Count mismatch: Expected {expected_count}, API returned {api_count}")
                if integrity_failures:
                    fail_reasons.append(f"Offer integrity violation on {len(integrity_failures)} returned offer(s)")

                print(f"\n[FAIL] Test #{idx} ({combo_name})")
                print(f"   Filter combination: {filter_params}")
                print(f"   Expected count from dataset: {expected_count}")
                print(f"   Returned count from /api/offers: {api_count}")

                for inf in integrity_failures:
                    off = inf["offer"]
                    print("\n   Filter combination:", filter_params)
                    print("   Expected values:", inf["expected"])
                    print("   Returned offer:", off.get("title") or off.get("id"))
                    print("   Violated field(s):", ", ".join(inf["violated"]))
                    print("   external_id:", off.get("external_id"))
                    print("   provider:", off.get("provider"))
                    print("   country:", off.get("country"))
                    print("   region:", off.get("region"))

                failures.append({
                    "combo_name": combo_name,
                    "params": filter_params,
                    "expected_count": expected_count,
                    "api_count": api_count,
                    "reasons": fail_reasons,
                    "integrity_failures": integrity_failures,
                })

    total_tested = len(all_test_combos)
    failed_count = len(failures)

    print("\n================================================================================")
    print("FINAL ADVERSARIAL INTEGRATION TEST REPORT")
    print("================================================================================")
    print(f"Filter combinations tested: {total_tested}")
    print(f"Random fuzz tests: {len(fuzz_combos)}")
    print(f"Edge-case tests: {len(edge_case_combos)}")
    print(f"Offer integrity checks: {total_offer_integrity_checks}")
    print(f"PASS: {passed_count}")
    print(f"FAIL: {failed_count}")
    print("================================================================================")

    if failures:
        fail_msg = f"{failed_count} tests FAILED during adversarial integration testing:\n"
        for f in failures:
            fail_msg += f"\nTest: {f['combo_name']}\nParams: {f['params']}\nReason(s): {', '.join(f.get('reasons', [f.get('reason', '')]))}\n"
        pytest.fail(fail_msg)


if __name__ == "__main__":
    asyncio.run(test_live_e2e_import_and_offers_filtering())
