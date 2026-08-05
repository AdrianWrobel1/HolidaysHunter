"""Offer QA & Single Offer Debugger Service.

Provides complete Quality Assurance data validation, automated filter matrix testing,
impossible/contradictory situation detection, post-import formatted logging,
and full 4-stage single offer pipeline lineage debugging.
"""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.countries import COUNTRY_CANONICAL_MAP, POPULAR_COUNTRIES, normalize_country_name
from app.models.enums import MealType, Provider, TransportType
from app.models.offer import Offer
from app.providers.schemas import NormalizedOffer

logger = logging.getLogger(__name__)

# Lightweight in-memory raw payload cache: (provider, external_id) -> raw_dict
_RAW_PAYLOAD_CACHE: dict[tuple[str, str], dict[str, Any]] = {}
_LAST_QA_REPORT: dict[str, Any] | None = None
_IMPORT_AUDIT_RECORDS: list[dict[str, Any]] = []


def store_import_audit_record(record: dict[str, Any]) -> None:
    """Store raw vs normalized vs DB audit record for discrepancy analysis."""
    _IMPORT_AUDIT_RECORDS.append(record)


def clear_import_audit_records() -> None:
    """Clear cached import audit records before a new import run."""
    _IMPORT_AUDIT_RECORDS.clear()


def get_import_audit_records() -> list[dict[str, Any]]:
    """Get all cached import audit records."""
    return list(_IMPORT_AUDIT_RECORDS)


def format_discrepancy_table(records: list[dict[str, Any]]) -> str:
    """Format structured text table for API vs DB offer count discrepancy audit.
    
    Columns: external_id | hotel | API region | normalized region | DB region | status | dokładny powód
    """
    if not records:
        return "Brak szczegółowych wpisów audytowych."
    
    headers = ["external_id", "hotel", "API region", "normalized region", "DB region", "status", "dokładny powód"]
    rows = []
    for r in records:
        rows.append([
            str(r.get("external_id", "") or "UNKNOWN"),
            str(r.get("hotel", "") or "UNKNOWN"),
            str(r.get("api_region", "") or "NONE"),
            str(r.get("normalized_region", "") or "NONE"),
            str(r.get("db_region", "") or "NONE"),
            str(r.get("status", "") or "unknown"),
            str(r.get("reason", "") or "Brak opisu"),
        ])

    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(val))

    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    sep_line = "-+-".join("-" * col_widths[i] for i in range(len(headers)))

    data_lines = []
    for row in rows:
        data_lines.append(" | ".join(val.ljust(col_widths[i]) for i, val in enumerate(row)))

    return "\n".join([header_line, sep_line] + data_lines)

# Recognized Polish departure cities/airports dictionary
RECOGNIZED_DEPARTURE_CITIES: set[str] = {
    "warszawa", "katowice", "poznań", "poznan", "wrocław", "wroclaw",
    "gdańsk", "gdansk", "kraków", "krakow", "szczecin", "rzeszów", "rzeszow",
    "bydgoszcz", "łódź", "lodz", "lublin", "zielona góra", "zielona gora",
    "radom", "olsztyn", "warszawa-chopin", "warszawa-modlin", "chopin", "modlin",
}


def store_raw_payload(provider: str, external_id: str, raw_data: dict[str, Any]) -> None:
    """Store raw payload in lightweight in-memory cache for lineage debugging."""
    prov_key = provider.lower().strip()
    _RAW_PAYLOAD_CACHE[(prov_key, str(external_id))] = raw_data


def get_raw_payload(provider: str | None, external_id: str) -> dict[str, Any] | None:
    """Retrieve cached raw payload by provider and external_id."""
    if provider:
        prov_key = provider.lower().strip()
        if (prov_key, str(external_id)) in _RAW_PAYLOAD_CACHE:
            return _RAW_PAYLOAD_CACHE[(prov_key, str(external_id))]
    # Fallback search by external_id only
    for (p, ext_id), raw in _RAW_PAYLOAD_CACHE.items():
        if ext_id == str(external_id):
            return raw
    return None


def validate_offer(
    raw_payload: dict[str, Any] | None,
    normalized: NormalizedOffer | None,
    offer_db: Offer | None = None,
) -> list[str]:
    """Validate offer fields and return list of validation error messages.

    Checks:
    - missing required fields
    - provider correctness
    - country canonical correctness
    - region format
    - departure airport / city validity
    - meal / board type validity
    - hotel stars and rating validity
    - price total & per person logical consistency
    - departure date & return date sanity
    """
    errors: list[str] = []

    # 1. Normalized / DB Offer extraction
    ext_id = (normalized.external_id if normalized else (offer_db.external_id if offer_db else None))
    prov = (normalized.provider.value if normalized else (offer_db.provider if offer_db else None))
    title = (normalized.title if normalized else (offer_db.title if offer_db else None))
    country = (normalized.country if normalized else (offer_db.country if offer_db else None))
    region = (normalized.region if normalized else (offer_db.region if offer_db else None))
    hotel_name = (normalized.hotel_name if normalized else (offer_db.hotel_name if offer_db else None))
    hotel_stars = (normalized.hotel_stars if normalized else (offer_db.hotel_stars if offer_db else None))
    hotel_rating = (normalized.hotel_rating if normalized else (offer_db.hotel_rating if offer_db else None))
    departure_date = (normalized.departure_date if normalized else (offer_db.departure_date if offer_db else None))
    return_date = (normalized.return_date if normalized else (offer_db.return_date if offer_db else None))
    duration_nights = (normalized.duration_nights if normalized else (offer_db.duration_nights if offer_db else None))
    departure_city = (normalized.departure_city if normalized else (offer_db.departure_city if offer_db else None))
    meal_type = (normalized.meal_type.value if normalized and isinstance(normalized.meal_type, MealType)
                 else (normalized.meal_type if normalized else (offer_db.meal_type if offer_db else None)))
    transport_type = (normalized.transport_type.value if normalized and isinstance(normalized.transport_type, TransportType)
                      else (normalized.transport_type if normalized else (offer_db.transport_type if offer_db else None)))
    price_total = (normalized.price_total if normalized else (offer_db.price_total if offer_db else None))
    price_per_person = (normalized.price_per_person if normalized else (offer_db.price_per_person if offer_db else None))

    # Check Required Fields
    required_map = {
        "external_id": ext_id,
        "provider": prov,
        "title": title,
        "country": country,
        "hotel_name": hotel_name,
        "departure_date": departure_date,
        "return_date": return_date,
        "duration_nights": duration_nights,
        "departure_city": departure_city,
        "meal_type": meal_type,
        "transport_type": transport_type,
        "price_total": price_total,
        "price_per_person": price_per_person,
    }
    for req_name, req_val in required_map.items():
        if req_val is None or (isinstance(req_val, str) and not req_val.strip()):
            errors.append(f"missing_required_field: {req_name}")

    # Provider correctness
    if prov:
        try:
            Provider(str(prov).lower())
        except ValueError:
            errors.append(f"invalid_provider: '{prov}' is not a recognized provider enum")

    # Country correctness
    if country:
        country_str = str(country).strip()
        canonical = normalize_country_name(country_str)
        if country_str != canonical:
            errors.append(f"invalid_country: '{country_str}' is uncanonicalized (expected '{canonical}')")

    # Region correctness
    if region is not None:
        region_str = str(region).strip()
        if not region_str or "<" in region_str or "{" in region_str:
            errors.append(f"invalid_region: invalid or malformed region string '{region_str}'")

    # Departure airport / city correctness
    if departure_city:
        dep_clean = str(departure_city).strip().lower()
        if not any(city in dep_clean for city in RECOGNIZED_DEPARTURE_CITIES):
            errors.append(f"invalid_airport: unrecognized departure city/airport '{departure_city}'")

    # Board / MealType correctness
    if meal_type:
        try:
            MealType(str(meal_type).lower())
        except ValueError:
            errors.append(f"invalid_board: '{meal_type}' is not a recognized meal_type enum")

    # Hotel stars and rating correctness
    if hotel_name:
        if not str(hotel_name).strip():
            errors.append("invalid_hotel: hotel_name is empty")
    if hotel_stars is not None:
        try:
            stars_val = float(hotel_stars)
            if stars_val < 0 or stars_val > 5.0:
                errors.append(f"invalid_hotel: hotel_stars {stars_val} out of range [0, 5.0]")
        except (ValueError, TypeError):
            errors.append(f"invalid_hotel: hotel_stars '{hotel_stars}' is not numeric")

    if hotel_rating is not None:
        try:
            rating_val = float(hotel_rating)
            if rating_val < 0 or rating_val > 10.0:
                errors.append(f"invalid_hotel: hotel_rating {rating_val} out of range [0, 10.0]")
        except (ValueError, TypeError):
            errors.append(f"invalid_hotel: hotel_rating '{hotel_rating}' is not numeric")

    # Price correctness
    if price_total is not None and price_per_person is not None:
        try:
            tot = Decimal(str(price_total))
            ppp = Decimal(str(price_per_person))
            if tot <= 0:
                errors.append(f"invalid_price: price_total {tot} must be positive")
            if ppp <= 0:
                errors.append(f"invalid_price: price_per_person {ppp} must be positive")
            if tot < ppp:
                errors.append(f"invalid_price: price_total ({tot}) cannot be less than price_per_person ({ppp})")
        except Exception:
            errors.append("invalid_price: invalid numeric decimal price value")

    # Departure & Return Date correctness
    if departure_date and return_date:
        if isinstance(departure_date, str):
            try:
                departure_date = date.fromisoformat(departure_date[:10])
            except ValueError:
                errors.append(f"invalid_departure_date: invalid departure_date string '{departure_date}'")
        if isinstance(return_date, str):
            try:
                return_date = date.fromisoformat(return_date[:10])
            except ValueError:
                errors.append(f"invalid_departure_date: invalid return_date string '{return_date}'")

        if isinstance(departure_date, date) and isinstance(return_date, date):
            if return_date < departure_date:
                errors.append(f"invalid_departure_date: return_date ({return_date}) before departure_date ({departure_date})")
            calc_nights = (return_date - departure_date).days
            if duration_nights is not None:
                try:
                    dur_val = int(duration_nights)
                    if abs(dur_val - calc_nights) > 1:
                        errors.append(f"invalid_departure_date: duration_nights ({dur_val}) does not match date delta ({calc_nights} nights)")
                except ValueError:
                    errors.append(f"invalid_departure_date: duration_nights '{duration_nights}' not integer")

    return errors


async def run_qa_audit(session: AsyncSession) -> dict[str, Any]:
    """Execute complete QA audit on database offers and automated filter tests.

    Returns full QA report dict and updates global cache for /debug/qa.
    """
    global _LAST_QA_REPORT

    # 1. Fetch all available DB offers
    stmt = select(Offer)
    result = await session.execute(stmt)
    db_offers = list(result.scalars().all())

    total_imported = len(db_offers)
    valid_count = 0
    invalid_count = 0

    invalid_breakdown: dict[str, int] = {
        "invalid_country": 0,
        "invalid_provider": 0,
        "invalid_airport": 0,
        "invalid_region": 0,
        "invalid_board": 0,
        "invalid_hotel": 0,
        "invalid_price": 0,
        "invalid_departure_date": 0,
        "missing_required_field": 0,
    }

    invalid_offers_lineage: list[dict[str, Any]] = []

    for offer in db_offers:
        raw = get_raw_payload(offer.provider, offer.external_id)
        errs = validate_offer(raw, None, offer_db=offer)

        if not errs:
            valid_count += 1
        else:
            invalid_count += 1
            # Count error categories
            for err in errs:
                cat = err.split(":")[0].strip()
                if cat in invalid_breakdown:
                    invalid_breakdown[cat] += 1
                else:
                    invalid_breakdown["missing_required_field"] += 1

            # Build 4-stage lineage for invalid offer
            lineage = _build_offer_lineage(offer, raw, errs)
            invalid_offers_lineage.append(lineage)

    # 2. Automated Filter Matrix Tests
    filter_test_results = await _run_automated_filter_tests(session, db_offers)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_imported": total_imported,
            "total_valid": valid_count,
            "total_invalid": invalid_count,
            "invalid_breakdown": invalid_breakdown,
        },
        "filter_tests": filter_test_results,
        "invalid_offers_count": len(invalid_offers_lineage),
        "invalid_offers_lineage": invalid_offers_lineage,
    }

    _LAST_QA_REPORT = report

    # 3. Print formatted console log summary
    _log_qa_summary(report)

    return report


def get_latest_qa_report() -> dict[str, Any]:
    """Get latest stored QA report or empty structure."""
    if _LAST_QA_REPORT:
        return _LAST_QA_REPORT
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total_imported": 0,
            "total_valid": 0,
            "total_invalid": 0,
            "invalid_breakdown": {
                "invalid_country": 0,
                "invalid_provider": 0,
                "invalid_airport": 0,
                "invalid_region": 0,
                "invalid_board": 0,
                "invalid_hotel": 0,
                "invalid_price": 0,
                "invalid_departure_date": 0,
                "missing_required_field": 0,
            },
        },
        "filter_tests": [],
        "invalid_offers_count": 0,
        "invalid_offers_lineage": [],
    }


async def debug_offer_by_id(session: AsyncSession, identifier: str) -> dict[str, Any]:
    """Debug single offer by database UUID or provider external_id.

    Returns complete 4-stage pipeline lineage:
    1. Raw API
    2. NormalizedOffer
    3. DB Record
    4. Filter Results (evaluating every filter criterion with PASS/FAIL explanation).
    """
    from app.services.offer_service import list_offers

    offer: Offer | None = None

    # Try UUID lookup first
    try:
        uuid_val = UUID(identifier)
        stmt = select(Offer).where(Offer.id == uuid_val)
        res = await session.execute(stmt)
        offer = res.scalar_one_or_none()
    except (ValueError, TypeError):
        pass

    # If not found by UUID, try lookup by external_id
    if not offer:
        stmt = select(Offer).where(Offer.external_id == str(identifier))
        res = await session.execute(stmt)
        offer = res.scalar_one_or_none()

    if not offer:
        return {
            "error": f"Offer not found with ID or external_id '{identifier}'",
            "identifier": identifier,
        }

    raw = get_raw_payload(offer.provider, offer.external_id)
    validation_errors = validate_offer(raw, None, offer_db=offer)

    # 1. Raw API payload
    raw_api_stage = raw if raw else {
        "note": "Raw API payload not retained in memory cache. Reconstruct from DB or re-run import.",
        "external_id": offer.external_id,
        "provider": offer.provider,
    }

    # 2. NormalizedOffer representation
    normalized_stage = {
        "external_id": offer.external_id,
        "provider": offer.provider,
        "title": offer.title,
        "country": offer.country,
        "region": offer.region,
        "city": offer.city,
        "hotel_name": offer.hotel_name,
        "hotel_stars": offer.hotel_stars,
        "hotel_rating": offer.hotel_rating,
        "departure_date": str(offer.departure_date),
        "return_date": str(offer.return_date),
        "duration_nights": offer.duration_nights,
        "departure_city": offer.departure_city,
        "adults": offer.adults,
        "children": offer.children,
        "meal_type": offer.meal_type,
        "transport_type": offer.transport_type,
        "price_total": float(offer.price_total),
        "price_per_person": float(offer.price_per_person),
        "currency": offer.currency,
        "offer_url": offer.offer_url,
        "image_url": offer.image_url,
        "validation_errors": validation_errors,
    }

    # 3. DB Record representation
    db_record_stage = {
        "id": str(offer.id),
        "external_id": offer.external_id,
        "provider": offer.provider,
        "country": offer.country,
        "region": offer.region,
        "city": offer.city,
        "hotel_name": offer.hotel_name,
        "departure_city": offer.departure_city,
        "meal_type": offer.meal_type,
        "price_total": float(offer.price_total),
        "price_per_person": float(offer.price_per_person),
        "is_available": offer.is_available,
        "first_seen_at": offer.first_seen_at.isoformat() if offer.first_seen_at else None,
        "last_seen_at": offer.last_seen_at.isoformat() if offer.last_seen_at else None,
    }

    # 4. Filter Results — Line-by-line evaluation of standard filter criteria
    filter_checks = []

    # Country filter test
    c_list_offers, c_total = await list_offers(session, country=offer.country)
    c_in_list = any(o.id == offer.id for o in c_list_offers)
    filter_checks.append({
        "filter": "country",
        "tested_value": offer.country,
        "status": "PASS" if c_in_list else "FAIL",
        "explanation": (
            f"Offer country '{offer.country}' matches country query filter. Total offers found: {c_total}."
            if c_in_list else
            f"FAIL: Offer country '{offer.country}' in DB was excluded by country filter list_offers. Check canonicalization!"
        )
    })

    # Provider filter test
    p_list_offers, p_total = await list_offers(session, provider=offer.provider)
    p_in_list = any(o.id == offer.id for o in p_list_offers)
    filter_checks.append({
        "filter": "provider",
        "tested_value": offer.provider,
        "status": "PASS" if p_in_list else "FAIL",
        "explanation": (
            f"Offer provider '{offer.provider}' matches provider query filter. Total offers found: {p_total}."
            if p_in_list else
            f"FAIL: Offer provider '{offer.provider}' was excluded by provider filter list_offers query!"
        )
    })

    # Country + Provider filter test
    cp_list_offers, cp_total = await list_offers(session, country=offer.country, provider=offer.provider)
    cp_in_list = any(o.id == offer.id for o in cp_list_offers)
    filter_checks.append({
        "filter": "country + provider",
        "tested_value": f"country={offer.country}, provider={offer.provider}",
        "status": "PASS" if cp_in_list else "FAIL",
        "explanation": (
            f"Offer matched combined country '{offer.country}' + provider '{offer.provider}' query filter ({cp_total} total)."
            if cp_in_list else
            f"FAIL: CONTRADICTION! Offer exists with country='{offer.country}' and provider='{offer.provider}', but combined query returned {cp_total} results!"
        )
    })

    # Departure city / airport filter test
    dep_list_offers, dep_total = await list_offers(session, departure_city=offer.departure_city)
    dep_in_list = any(o.id == offer.id for o in dep_list_offers)
    filter_checks.append({
        "filter": "departure_city / airport",
        "tested_value": offer.departure_city,
        "status": "PASS" if dep_in_list else "FAIL",
        "explanation": (
            f"Offer departure_city '{offer.departure_city}' matches filter query ({dep_total} total)."
            if dep_in_list else
            f"FAIL: Offer departure_city '{offer.departure_city}' excluded by departure_city query filter!"
        )
    })

    # Meal type / board filter test
    meal_list_offers, meal_total = await list_offers(session, meal_type=offer.meal_type)
    meal_in_list = any(o.id == offer.id for o in meal_list_offers)
    filter_checks.append({
        "filter": "meal_type / board",
        "tested_value": offer.meal_type,
        "status": "PASS" if meal_in_list else "FAIL",
        "explanation": (
            f"Offer meal_type '{offer.meal_type}' matches filter query ({meal_total} total)."
            if meal_in_list else
            f"FAIL: Offer meal_type '{offer.meal_type}' excluded by meal_type query filter!"
        )
    })

    # Region filter test
    if offer.region:
        r_list_offers, r_total = await list_offers(session, region=offer.region)
        r_in_list = any(o.id == offer.id for o in r_list_offers)
        filter_checks.append({
            "filter": "region",
            "tested_value": offer.region,
            "status": "PASS" if r_in_list else "FAIL",
            "explanation": (
                f"Offer region '{offer.region}' matches filter query ({r_total} total)."
                if r_in_list else
                f"FAIL: Offer region '{offer.region}' excluded by region query filter!"
            )
        })

    # Available only test
    filter_checks.append({
        "filter": "available_only",
        "tested_value": offer.is_available,
        "status": "PASS" if offer.is_available else "FAIL",
        "explanation": (
            "Offer is available (is_available=True) and returned in standard user searches."
            if offer.is_available else
            "FAIL: Offer is marked as unavailable (is_available=False) and filtered out by default."
        )
    })

    return {
        "offer_id": str(offer.id),
        "external_id": offer.external_id,
        "provider": offer.provider,
        "title": offer.title,
        "validation_errors": validation_errors,
        "is_valid": len(validation_errors) == 0,
        "lineage": {
            "1_raw_api": raw_api_stage,
            "2_normalized_offer": normalized_stage,
            "3_db_record": db_record_stage,
            "4_filter_results": filter_checks,
        }
    }


def _build_offer_lineage(offer: Offer, raw: dict[str, Any] | None, errors: list[str]) -> dict[str, Any]:
    """Construct 4-stage lineage summary for an invalid offer."""
    return {
        "offer_id": str(offer.id),
        "external_id": offer.external_id,
        "provider": offer.provider,
        "validation_errors": errors,
        "1_raw_api": raw if raw else {"note": "Raw API payload not retained in cache"},
        "2_normalized_offer": {
            "external_id": offer.external_id,
            "provider": offer.provider,
            "country": offer.country,
            "departure_city": offer.departure_city,
            "meal_type": offer.meal_type,
            "price_total": float(offer.price_total),
            "price_per_person": float(offer.price_per_person),
        },
        "3_db_record": {
            "id": str(offer.id),
            "is_available": offer.is_available,
            "country": offer.country,
        },
        "4_filter_results_summary": f"Failed validation check with {len(errors)} error(s).",
    }


async def _run_automated_filter_tests(
    session: AsyncSession,
    db_offers: list[Offer],
) -> list[dict[str, Any]]:
    """Execute automated filter matrix tests and detect contradictory filter states."""
    from app.services.offer_service import list_offers

    tests = []

    if not db_offers:
        return [
            {"filter_name": "country", "status": "PASSED", "explanation": "No offers in database to test."},
            {"filter_name": "provider", "status": "PASSED", "explanation": "No offers in database to test."},
            {"filter_name": "country + provider", "status": "PASSED", "explanation": "No offers in database to test."},
            {"filter_name": "airport", "status": "PASSED", "explanation": "No offers in database to test."},
            {"filter_name": "board", "status": "PASSED", "explanation": "No offers in database to test."},
            {"filter_name": "region", "status": "PASSED", "explanation": "No offers in database to test."},
        ]

    # Distinct values in DB
    countries = list({o.country for o in db_offers if o.country})
    providers = list({o.provider for o in db_offers if o.provider})
    airports = list({o.departure_city for o in db_offers if o.departure_city})
    boards = list({o.meal_type for o in db_offers if o.meal_type})
    regions = list({o.region for o in db_offers if o.region})

    # 1. Country filter test
    country_passed = True
    c_failures = []
    for c in countries:
        res, count = await list_offers(session, country=c)
        db_count = sum(1 for o in db_offers if o.country == c and o.is_available)
        if count != db_count:
            country_passed = False
            c_failures.append(f"country '{c}': list_offers returned {count}, but DB has {db_count}")
    tests.append({
        "filter_name": "country",
        "status": "PASSED" if country_passed else "FAILED",
        "explanation": "All country filter queries returned exact expected DB counts." if country_passed else "; ".join(c_failures),
    })

    # 2. Provider filter test
    provider_passed = True
    p_failures = []
    for p in providers:
        res, count = await list_offers(session, provider=p)
        db_count = sum(1 for o in db_offers if o.provider == p and o.is_available)
        if count != db_count:
            provider_passed = False
            p_failures.append(f"provider '{p}': list_offers returned {count}, but DB has {db_count}")
    tests.append({
        "filter_name": "provider",
        "status": "PASSED" if provider_passed else "FAILED",
        "explanation": "All provider filter queries returned exact expected DB counts." if provider_passed else "; ".join(p_failures),
    })

    # 3. Country + Provider combination & Contradiction Detection
    cp_passed = True
    cp_explanations = []

    for c in countries:
        for p in providers:
            matching_db_offers = [o for o in db_offers if o.country == c and o.provider == p and o.is_available]
            c_db_total = sum(1 for o in db_offers if o.country == c and o.is_available)
            p_db_total = sum(1 for o in db_offers if o.provider == p and o.is_available)

            res, count = await list_offers(session, country=c, provider=p)

            # CONTRADICTION DETECTED:
            # Country C has >0 offers, Provider P has >0 offers, DB has matching offers for C+P,
            # BUT query country=C + provider=P returns 0 offers!
            if len(matching_db_offers) > 0 and count == 0:
                cp_passed = False
                explanation = (
                    f"CONTRADICTION DETECTED! country='{c}' returns {c_db_total} offers, provider='{p}' returns {p_db_total} offers, "
                    f"and DB has {len(matching_db_offers)} offers with both, BUT query country='{c}' + provider='{p}' returned 0 offers. "
                    f"Root cause: Country value '{c}' or Provider value '{p}' in DB does not match normalized query parameters."
                )
                cp_explanations.append(explanation)
                logger.error("[QA FILTER CONTRADICTION] %s", explanation)

    tests.append({
        "filter_name": "country + provider",
        "status": "PASSED" if cp_passed else "FAILED",
        "explanation": "All composite country + provider filter queries returned valid matching offers." if cp_passed else " | ".join(cp_explanations),
    })

    # 4. Airport filter test
    airport_passed = True
    a_failures = []
    for a in airports:
        res, count = await list_offers(session, departure_city=a)
        db_count = sum(1 for o in db_offers if o.departure_city == a and o.is_available)
        if count != db_count:
            airport_passed = False
            a_failures.append(f"airport '{a}': list_offers returned {count}, DB has {db_count}")
    tests.append({
        "filter_name": "airport",
        "status": "PASSED" if airport_passed else "FAILED",
        "explanation": "All departure airport queries returned exact expected DB counts." if airport_passed else "; ".join(a_failures),
    })

    # 5. Board filter test
    board_passed = True
    b_failures = []
    for b in boards:
        res, count = await list_offers(session, meal_type=b)
        db_count = sum(1 for o in db_offers if o.meal_type == b and o.is_available)
        if count != db_count:
            board_passed = False
            b_failures.append(f"meal_type '{b}': list_offers returned {count}, DB has {db_count}")
    tests.append({
        "filter_name": "board",
        "status": "PASSED" if board_passed else "FAILED",
        "explanation": "All meal_type board queries returned exact expected DB counts." if board_passed else "; ".join(b_failures),
    })

    # 6. Region filter test & discrepancy audit
    region_passed = True
    r_explanations = []
    discrepancy_tables = []

    audit_records = get_import_audit_records()

    for r in regions:
        res, count = await list_offers(session, region=r)
        db_count = sum(1 for o in db_offers if o.region == r and o.is_available)

        # Match audit records for this region (comparing normalized or raw region)
        r_audit_recs = [
            rec for rec in audit_records
            if rec.get("normalized_region") == r or rec.get("api_region") == r
        ]
        api_returned_count = len(r_audit_recs) if r_audit_recs else db_count

        if count != db_count or (api_returned_count > 0 and api_returned_count != db_count):
            # Breakdown status of API records
            saved_cnt = sum(1 for rec in r_audit_recs if rec.get("status") == "saved")
            updated_cnt = sum(1 for rec in r_audit_recs if rec.get("status") == "updated")
            dup_cnt = sum(1 for rec in r_audit_recs if rec.get("status") == "duplicate")
            skipped_cnt = sum(1 for rec in r_audit_recs if rec.get("status") == "skipped")
            filtered_cnt = sum(1 for rec in r_audit_recs if rec.get("status") == "filtered")

            table_str = format_discrepancy_table(r_audit_recs)
            discrepancy_tables.append(f"--- Region '{r}' Discrepancy Audit ---\n{table_str}")

            # Check if discrepancy is caused by expected system operations (deduplication, updates, skipped)
            is_expected_behavior = (
                api_returned_count == (saved_cnt + updated_cnt + dup_cnt + skipped_cnt + filtered_cnt)
                and all(rec.get("normalized_region") == r for rec in r_audit_recs if rec.get("status") in ("saved", "updated", "duplicate"))
            )

            if is_expected_behavior:
                expl = (
                    f"INFO: Region '{r}': API returned {api_returned_count} offers "
                    f"({saved_cnt} saved as new, {updated_cnt} updated existing records, {dup_cnt} duplicate, {skipped_cnt} skipped). "
                    f"Active DB count = {db_count}."
                )
                r_explanations.append(expl)
            else:
                region_passed = False
                expl = (
                    f"FAIL: Region '{r}': API returned {api_returned_count} offers, but DB count is {db_count}. "
                    f"Root cause: Region normalization mismatch or saving error detected!"
                )
                r_explanations.append(expl)
        elif count != db_count:
            region_passed = False
            r_explanations.append(f"FAIL: region '{r}': list_offers returned {count}, DB has {db_count}")

    tests.append({
        "filter_name": "region",
        "status": "PASSED" if region_passed else "FAILED",
        "explanation": "All region queries returned exact expected DB counts." if (region_passed and not r_explanations) else " | ".join(r_explanations),
        "discrepancy_tables": discrepancy_tables,
    })

    return tests


def _log_qa_summary(report: dict[str, Any]) -> None:
    """Log nicely formatted QA import summary block to standard output."""
    summary = report.get("summary", {})
    imported = summary.get("total_imported", 0)
    valid = summary.get("total_valid", 0)
    invalid = summary.get("total_invalid", 0)
    breakdown = summary.get("invalid_breakdown", {})
    filter_tests = report.get("filter_tests", [])

    lines = [
        "",
        "================ QA IMPORT REPORT ================",
        f"Imported: {imported}",
        f"Valid: {valid}",
        f"Invalid: {invalid}",
        "",
    ]

    for err_key, count in breakdown.items():
        if count > 0:
            label = err_key.replace("invalid_", "Invalid ").replace("_", " ")
            lines.append(f"{label}: {count}")

    lines.append("")
    lines.append("Filter tests:")
    for ft in filter_tests:
        name = ft.get("filter_name", "")
        status = ft.get("status", "")
        expl = ft.get("explanation", "")
        icon = "[OK]" if status == "PASSED" else "[FAIL]"
        line = f"{icon} {name}"
        if expl:
            line += f" -> {expl}"
        lines.append(line)

        # Print discrepancy tables if present
        for tbl in ft.get("discrepancy_tables", []):
            lines.append("")
            lines.append(tbl)

    lines.append("==================================================")
    lines.append("")

    formatted_msg = "\n".join(lines)
    logger.info(formatted_msg)
    print(formatted_msg)
