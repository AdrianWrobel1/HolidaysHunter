"""Offer query service — filtering, sorting, pagination, and detail retrieval.

All database query logic for the Explorer lives here.
API endpoints delegate to these functions and never build queries directly.
"""

import logging
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.countries import (
    normalize_country_name,
    normalize_provider_name,
    normalize_region_name,
)
from app.models.offer import Offer
from app.models.price_history import PriceHistory

logger = logging.getLogger(__name__)


async def list_offers(
    session: AsyncSession,
    *,
    country: str | list[str] | None = None,
    region: str | list[str] | None = None,
    provider: str | list[str] | None = None,
    departure_city: str | list[str] | None = None,
    meal_type: str | list[str] | None = None,
    transport_type: str | None = None,
    hotel_stars: float | list[float] | None = None,
    hotel_stars_min: float | None = None,
    price_min: Decimal | None = None,
    price_max: Decimal | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    duration_min: int | None = None,
    duration_max: int | None = None,
    adults: int | None = None,
    children: int | None = None,
    search: str | None = None,
    available_only: bool = True,
    sort_by: str = "price_per_person",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Offer], int]:
    """Build and execute a filtered, sorted, paginated offers query.

    Returns:
        Tuple of (offers, total_count).
    """
    logger.info(
        "[offer_service] list_offers called: country=%r, region=%r, provider=%r, available_only=%s, page=%d/%d",
        country, region, provider, available_only, page, page_size,
    )

    # Normalize filter parameters on Python side to ensure exact SQL equality can utilize indexes
    # --- Step-by-step filter application & logging ---
    # Log initial DB total and example offer
    init_total_stmt = select(func.count(Offer.id))
    initial_db_count = (await session.execute(init_total_stmt)).scalar_one()

    init_example_res = await session.execute(select(Offer).limit(1))
    init_example = init_example_res.scalar_one_or_none()
    ex_init_str = f"({init_example.provider}, {init_example.country}, {init_example.region})" if init_example else "NONE"

    filter_logs = [f"Initial: {initial_db_count} [example: {ex_init_str}]"]

    # Define filter conditions sequence
    filter_conditions = []

    if available_only:
        filter_conditions.append(("available_only", Offer.is_available.is_(True)))

    if country is not None:
        if isinstance(country, list):
            norm_c = [normalize_country_name(c) for c in country if c and str(c).strip()]
            if norm_c:
                filter_conditions.append(("country", Offer.country.in_(norm_c)))
            else:
                filter_conditions.append(("country", Offer.id.in_([])))
        elif isinstance(country, str):
            c_str = country.strip()
            if c_str:
                norm_c = normalize_country_name(c_str)
                filter_conditions.append(("country", Offer.country == norm_c))
            else:
                filter_conditions.append(("country", Offer.id.in_([])))

    if region is not None:
        if isinstance(region, list):
            norm_r = [normalize_region_name(r) for r in region if r and str(r).strip() and normalize_region_name(r)]
            if norm_r:
                filter_conditions.append(("region", Offer.region.in_(norm_r)))
            else:
                filter_conditions.append(("region", Offer.id.in_([])))
        elif isinstance(region, str):
            r_str = region.strip()
            if r_str:
                norm_r = normalize_region_name(r_str)
                filter_conditions.append(("region", Offer.region == norm_r))
            else:
                filter_conditions.append(("region", Offer.id.in_([])))

    if provider is not None:
        if isinstance(provider, list):
            norm_p = [normalize_provider_name(p) for p in provider if p and str(p).strip() and normalize_provider_name(p)]
            if norm_p:
                filter_conditions.append(("provider", Offer.provider.in_(norm_p)))
            else:
                filter_conditions.append(("provider", Offer.id.in_([])))
        elif isinstance(provider, str):
            p_str = provider.strip()
            if p_str:
                norm_p = normalize_provider_name(p_str)
                filter_conditions.append(("provider", Offer.provider == norm_p))
            else:
                filter_conditions.append(("provider", Offer.id.in_([])))

    if departure_city is not None:
        if isinstance(departure_city, list):
            dep_conds = [Offer.departure_city.ilike(f"%{c.strip()}%") for c in departure_city if c and str(c).strip()]
            if dep_conds:
                filter_conditions.append(("departure_city", or_(*dep_conds)))
            else:
                filter_conditions.append(("departure_city", Offer.id.in_([])))
        elif isinstance(departure_city, str):
            d_str = departure_city.strip()
            if d_str:
                filter_conditions.append(("departure_city", Offer.departure_city.ilike(f"%{d_str}%")))
            else:
                filter_conditions.append(("departure_city", Offer.id.in_([])))

    if meal_type is not None:
        def _norm_meal(m: Any) -> str:
            return str(m).lower().strip().replace(" ", "_").replace("-", "_")

        if isinstance(meal_type, list):
            norm_m = [_norm_meal(m) for m in meal_type if m and str(m).strip()]
            if norm_m:
                filter_conditions.append(("meal_type", Offer.meal_type.in_(norm_m)))
            else:
                filter_conditions.append(("meal_type", Offer.id.in_([])))
        elif isinstance(meal_type, str):
            m_str = meal_type.strip()
            if m_str:
                filter_conditions.append(("meal_type", Offer.meal_type == _norm_meal(m_str)))
            else:
                filter_conditions.append(("meal_type", Offer.id.in_([])))

    if transport_type:
        filter_conditions.append(("transport_type", Offer.transport_type == transport_type))

    if hotel_stars:
        if isinstance(hotel_stars, list):
            valid_stars = [float(s) for s in hotel_stars if s is not None and 0 <= float(s) <= 9.9]
            if valid_stars:
                filter_conditions.append(("hotel_stars", Offer.hotel_stars.in_(valid_stars)))
            else:
                filter_conditions.append(("hotel_stars", Offer.id.in_([])))
        else:
            try:
                s_val = float(hotel_stars)
                if 0 <= s_val <= 9.9:
                    filter_conditions.append(("hotel_stars", Offer.hotel_stars == s_val))
                else:
                    filter_conditions.append(("hotel_stars", Offer.id.in_([])))
            except (ValueError, TypeError):
                filter_conditions.append(("hotel_stars", Offer.id.in_([])))
    elif hotel_stars_min is not None:
        try:
            s_min = float(hotel_stars_min)
            if 0 <= s_min <= 9.9:
                filter_conditions.append(("hotel_stars_min", Offer.hotel_stars >= s_min))
            elif s_min > 9.9:
                filter_conditions.append(("hotel_stars_min", Offer.id.in_([])))
            else:
                filter_conditions.append(("hotel_stars_min", Offer.hotel_stars >= 0))
        except (ValueError, TypeError):
            pass

    if price_min is not None:
        filter_conditions.append(("price_min", Offer.price_per_person >= price_min))

    if price_max is not None:
        filter_conditions.append(("price_max", Offer.price_per_person <= price_max))

    if date_from:
        filter_conditions.append(("date_from", Offer.departure_date >= date_from))

    if date_to:
        filter_conditions.append(("date_to", Offer.departure_date <= date_to))

    if duration_min is not None:
        filter_conditions.append(("duration_min", Offer.duration_nights >= duration_min))

    if duration_max is not None:
        filter_conditions.append(("duration_max", Offer.duration_nights <= duration_max))

    if adults is not None:
        filter_conditions.append(("adults", Offer.adults == adults))

    if children is not None:
        filter_conditions.append(("children", Offer.children == children))

    if search:
        pattern = f"%{search}%"
        filter_conditions.append(("search", or_(
            Offer.hotel_name.ilike(pattern),
            Offer.country.ilike(pattern),
            Offer.region.ilike(pattern),
            Offer.city.ilike(pattern),
            Offer.title.ilike(pattern),
        )))

    # Apply each filter step, count remaining records and fetch one example offer
    active_conditions = []
    for filter_name, condition in filter_conditions:
        active_conditions.append(condition)

        step_count_stmt = select(func.count(Offer.id)).where(*active_conditions)
        try:
            raw_cnt = (await session.execute(step_count_stmt)).scalar_one()
            step_count = int(raw_cnt) if isinstance(raw_cnt, (int, float)) else 0
        except Exception:
            step_count = 0

        if step_count > 0:
            step_example_stmt = select(Offer.provider, Offer.country, Offer.region).where(*active_conditions).limit(1)
            try:
                step_ex_res = await session.execute(step_example_stmt)
                step_ex_row = step_ex_res.first() if hasattr(step_ex_res, "first") else None
                if step_ex_row and isinstance(step_ex_row, (tuple, list)) and len(step_ex_row) >= 3:
                    ex_str = f"({step_ex_row[0]}, {step_ex_row[1]}, {step_ex_row[2]})"
                elif step_ex_row and hasattr(step_ex_row, "provider"):
                    ex_str = f"({step_ex_row.provider}, {step_ex_row.country}, {step_ex_row.region})"
                else:
                    ex_str = "NONE"
            except Exception:
                ex_str = "NONE"
        else:
            ex_str = "NONE"

        filter_logs.append(f"after {filter_name}: {step_count} [example: {ex_str}]")

    logger.info("[offer_service] Step-by-step filter counts: %s", " -> ".join(filter_logs))

    # Apply all accumulated conditions to primary query statement
    stmt = select(Offer)
    for cond in active_conditions:
        stmt = stmt.where(cond)

    count_stmt = select(func.count(Offer.id)).where(*active_conditions)
    try:
        total = (await session.execute(count_stmt)).scalar_one()
        if not isinstance(total, int):
            total = int(total) if isinstance(total, float) else 0
    except Exception:
        total = 0

    sort_column = _get_sort_column(sort_by)
    if sort_order == "desc":
        stmt = stmt.order_by(sort_column.desc().nulls_last())
    else:
        stmt = stmt.order_by(sort_column.asc().nulls_last())

    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(stmt)
    offers = list(result.scalars().all())

    return offers, total


def _get_sort_column(sort_by: str):
    """Map sort_by string to SQLAlchemy column."""
    columns = {
        "price_per_person": Offer.price_per_person,
        "price_total": Offer.price_total,
        "travel_score": Offer.travel_score,
        "departure_date": Offer.departure_date,
        "hotel_stars": Offer.hotel_stars,
        "hotel_rating": Offer.hotel_rating,
        "duration_nights": Offer.duration_nights,
    }
    return columns.get(sort_by, Offer.price_per_person)


async def get_offer_detail(
    offer_id: UUID,
    session: AsyncSession,
) -> Offer | None:
    """Fetch a single offer with its price history eagerly loaded."""
    stmt = (
        select(Offer)
        .options(selectinload(Offer.price_history))
        .where(Offer.id == offer_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def compute_price_change_pct(offer: Offer) -> float | None:
    """Percentage price change from earliest to current price.

    Returns negative values for price drops, positive for increases.
    Returns None if fewer than 2 price history entries exist.
    """
    if not offer.price_history or len(offer.price_history) < 2:
        return None

    sorted_history = sorted(offer.price_history, key=lambda ph: ph.recorded_at)
    first_price = sorted_history[0].price_per_person
    current_price = sorted_history[-1].price_per_person

    if first_price == 0:
        return None

    return round(float((current_price - first_price) / first_price * 100), 1)


def compute_days_available(offer: Offer) -> int:
    """Number of days since the offer was first seen."""
    now = datetime.now(timezone.utc)
    first_seen = offer.first_seen_at
    if first_seen.tzinfo is None:
        first_seen = first_seen.replace(tzinfo=timezone.utc)
    return max((now - first_seen).days, 0)


async def get_price_history(
    offer_id: UUID,
    session: AsyncSession,
) -> list[PriceHistory] | None:
    """Fetch price history for an offer, ordered chronologically.

    Returns None if the offer does not exist.
    """
    offer_exists = (
        await session.execute(select(func.count()).where(Offer.id == offer_id))
    ).scalar_one()

    if not offer_exists:
        return None

    stmt = (
        select(PriceHistory)
        .where(PriceHistory.offer_id == offer_id)
        .order_by(PriceHistory.recorded_at.asc())
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_filter_options(session: AsyncSession) -> dict[str, Any]:
    """Fetch distinct values for Explorer filter dropdowns.

    Only considers available offers to avoid showing stale filter values.
    Includes default fallback values for countries and providers if DB is empty.
    """
    from app.core.countries import POPULAR_COUNTRIES

    available_filter = Offer.is_available.is_(True)

    async def _distinct_values(column) -> list[str]:
        stmt = (
            select(column)
            .where(available_filter)
            .where(column.isnot(None))
            .distinct()
            .order_by(column.asc())
        )
        result = await session.execute(stmt)
        return [str(v) for v in result.scalars().all()]

    db_countries = await _distinct_values(Offer.country)
    # Merge DB countries with popular countries list preserving order
    countries_set = set(db_countries)
    all_countries = list(db_countries)
    for pc in POPULAR_COUNTRIES:
        if pc not in countries_set:
            all_countries.append(pc)
            countries_set.add(pc)

    regions = await _distinct_values(Offer.region)
    departure_cities = await _distinct_values(Offer.departure_city)
    db_providers = await _distinct_values(Offer.provider)

    default_providers = ["itaka", "tui", "wakacje_pl", "rainbow"]
    prov_set = set(db_providers)
    all_providers = list(db_providers)
    for dp in default_providers:
        if dp not in prov_set:
            all_providers.append(dp)
            prov_set.add(dp)

    meal_types = await _distinct_values(Offer.meal_type)
    transport_types = await _distinct_values(Offer.transport_type)

    # Build country -> regions mapping
    cr_stmt = (
        select(Offer.country, Offer.region)
        .where(available_filter)
        .where(Offer.country.isnot(None))
        .where(Offer.region.isnot(None))
        .distinct()
    )
    from app.core.countries import DEFAULT_COUNTRY_REGIONS

    country_regions: dict[str, list[str]] = {
        c: list(rgns) for c, rgns in DEFAULT_COUNTRY_REGIONS.items()
    }
    cr_result = await session.execute(cr_stmt)
    for cntry, rgn in cr_result.all():
        if cntry and rgn:
            country_regions.setdefault(cntry, []).append(rgn)

    for c in country_regions:
        country_regions[c] = sorted(list(set(country_regions[c])))

    return {
        "countries": sorted(all_countries),
        "regions": regions,
        "country_regions": country_regions,
        "departure_cities": departure_cities,
        "providers": sorted(all_providers),
        "meal_types": meal_types,
        "transport_types": transport_types,
    }


async def get_seasonal_trends(
    session: AsyncSession,
    country: str | None = None,
    region: str | None = None,
) -> list[dict]:
    """Calculate seasonal price trends (avg, min, max price per month) grouped by country and region."""
    month_col = func.extract("month", Offer.departure_date).label("month")
    stmt = (
        select(
            Offer.country,
            Offer.region,
            month_col,
            func.avg(Offer.price_per_person).label("avg_price"),
            func.min(Offer.price_per_person).label("min_price"),
            func.max(Offer.price_per_person).label("max_price"),
            func.count(Offer.id).label("offer_count"),
        )
        .where(Offer.departure_date.isnot(None), Offer.country.isnot(None))
    )
    if country:
        stmt = stmt.where(Offer.country == country)
    if region:
        stmt = stmt.where(Offer.region == region)

    stmt = stmt.group_by(Offer.country, Offer.region, month_col).order_by(
        Offer.country.asc(), Offer.region.asc(), month_col.asc()
    )
    result = await session.execute(stmt)

    month_names = {
        1: "Styczeń",
        2: "Luty",
        3: "Marzec",
        4: "Kwiecień",
        5: "Maj",
        6: "Czerwiec",
        7: "Lipiec",
        8: "Sierpień",
        9: "Wrzesień",
        10: "Październik",
        11: "Listopad",
        12: "Grudzień",
    }

    def _get_season(month: int) -> str:
        if month in (12, 1, 2):
            return "Zima ❄️"
        elif month in (3, 4, 5):
            return "Wiosna 🌸"
        elif month in (6, 7, 8):
            return "Lato ☀️"
        else:
            return "Jesień 🍂"

    trends = []
    for row in result.all():
        cntry, rgn, m_num, avg_p, min_p, max_p, count = row
        m_int = int(m_num) if m_num is not None else 1
        trends.append({
            "country": cntry,
            "region": rgn or "Wszystkie regiony",
            "month": m_int,
            "month_name": month_names.get(m_int, f"Miesiąc {m_int}"),
            "season": _get_season(m_int),
            "avg_price": round(float(avg_p), 2) if avg_p else 0,
            "min_price": round(float(min_p), 2) if min_p else 0,
            "max_price": round(float(max_p), 2) if max_p else 0,
            "offer_count": count,
        })
    return trends


async def delete_offer(session: AsyncSession, offer_id: UUID) -> bool:
    """Delete a single offer and its related records from database."""
    from sqlalchemy import delete
    from app.models.alert_event import AlertEvent
    from app.models.price_history import PriceHistory

    # Clean up alert events and price history first
    await session.execute(delete(AlertEvent).where(AlertEvent.offer_id == offer_id))
    await session.execute(delete(PriceHistory).where(PriceHistory.offer_id == offer_id))

    stmt = select(Offer).where(Offer.id == offer_id)
    result = await session.execute(stmt)
    offer = result.scalar_one_or_none()
    if not offer:
        return False
    await session.delete(offer)
    return True


async def clear_all_offers(session: AsyncSession) -> int:
    """Delete all offers and related records from database."""
    from sqlalchemy import delete
    from app.models.alert_event import AlertEvent
    from app.models.price_history import PriceHistory

    stmt = select(func.count(Offer.id))
    count = (await session.execute(stmt)).scalar() or 0

    await session.execute(delete(AlertEvent))
    await session.execute(delete(PriceHistory))
    await session.execute(delete(Offer))
    return count

