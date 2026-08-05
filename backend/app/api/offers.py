"""Offers API endpoints — Explorer."""

import math
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import (
    FilterOptionsResponse,
    OfferDetailResponse,
    OfferResponse,
    OffersListResponse,
    PriceHistoryResponse,
)
from app.database.session import get_session
from app.services.offer_service import (
    compute_days_available,
    compute_price_change_pct,
    get_filter_options,
    get_offer_detail,
    get_price_history,
    list_offers,
)

router = APIRouter(prefix="/api/offers", tags=["offers"])

ALLOWED_SORT_FIELDS = {
    "price_per_person",
    "price_total",
    "travel_score",
    "departure_date",
    "hotel_stars",
    "hotel_rating",
    "duration_nights",
}


@router.get("", response_model=OffersListResponse)
async def list_offers_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    country: list[str] | str | None = Query(None),
    region: list[str] | str | None = Query(None),
    provider: list[str] | str | None = Query(None),
    departure_city: list[str] | str | None = Query(None),
    meal_type: list[str] | str | None = Query(None),
    transport_type: str | None = Query(None),
    hotel_stars: list[float] | float | None = Query(None),
    hotel_stars_min: float | None = Query(None, ge=1, le=5),
    price_min: Decimal | None = Query(None, ge=0),
    price_max: Decimal | None = Query(None, ge=0),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    duration_min: int | None = Query(None, ge=1),
    duration_max: int | None = Query(None, ge=1),
    adults: int | None = Query(None, ge=1),
    children: int | None = Query(None, ge=0),
    search: str | None = Query(None, min_length=2, max_length=100),
    available_only: bool = Query(True),
    sort_by: str = Query("price_per_person"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    session: AsyncSession = Depends(get_session),
) -> OffersListResponse:
    """List offers with full filtering, sorting, and pagination."""
    if sort_by not in ALLOWED_SORT_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort_by value. Allowed: {', '.join(sorted(ALLOWED_SORT_FIELDS))}",
        )

    # Normalize single value / list parameters
    cntries = [country] if isinstance(country, str) else country
    rgns = [region] if isinstance(region, str) else region
    provs = [provider] if isinstance(provider, str) else provider
    dep_cities = [departure_city] if isinstance(departure_city, str) else departure_city
    meals = [meal_type] if isinstance(meal_type, str) else meal_type
    stars = [hotel_stars] if isinstance(hotel_stars, (int, float)) else hotel_stars

    offers, total = await list_offers(
        session,
        country=cntries,
        region=rgns,
        provider=provs,
        departure_city=dep_cities,
        meal_type=meals,
        transport_type=transport_type,
        hotel_stars=stars,
        hotel_stars_min=hotel_stars_min,
        price_min=price_min,
        price_max=price_max,
        date_from=date_from,
        date_to=date_to,
        duration_min=duration_min,
        duration_max=duration_max,
        adults=adults,
        children=children,
        search=search,
        available_only=available_only,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    return OffersListResponse(
        offers=[OfferResponse.model_validate(o) for o in offers],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.get("/filters", response_model=FilterOptionsResponse)
async def get_filters_endpoint(
    session: AsyncSession = Depends(get_session),
) -> FilterOptionsResponse:
    """Return available filter values for the Explorer UI."""
    options = await get_filter_options(session)
    return FilterOptionsResponse(**options)


@router.get("/seasonal-trends")
async def get_seasonal_trends_endpoint(
    country: str | None = Query(None),
    region: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Get monthly/seasonal average and min/max prices per country and region."""
    from app.services.offer_service import get_seasonal_trends
    return await get_seasonal_trends(session, country=country, region=region)


@router.post("/fetch-live")
async def fetch_live_offers_endpoint(
    provider: list[str] | str | None = Query(None),
    country: list[str] | str | None = Query(None),
    region: list[str] | str | None = Query(None),
    departure_city: list[str] | str | None = Query(None),
    meal_type: list[str] | str | None = Query(None),
    hotel_stars: list[float] | float | None = Query(None),
    price_max: Decimal | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    adults: int | None = Query(None, ge=1),
    children: int | None = Query(None, ge=0),
    duration_min: int | None = Query(None, ge=1),
    duration_max: int | None = Query(None, ge=1),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Fetch live offers from travel providers on demand, matching active filters."""
    from app.core.countries import normalize_provider_name
    from app.models.enums import Provider
    from app.services.import_service import run_import
    from app.services.qa_service import run_qa_audit

    cntries = [country] if isinstance(country, str) else country
    rgns = [region] if isinstance(region, str) else region
    dep_cities = [departure_city] if isinstance(departure_city, str) else departure_city
    meals = [meal_type] if isinstance(meal_type, str) else meal_type
    stars = [hotel_stars] if isinstance(hotel_stars, (int, float)) else hotel_stars
    prov_list = [provider] if isinstance(provider, str) else provider

    filter_params = {
        "country": cntries,
        "region": rgns,
        "provider": prov_list,
        "departure_city": dep_cities,
        "meal_type": meals,
        "hotel_stars": stars,
        "price_max": float(price_max) if price_max is not None else None,
        "date_from": str(date_from) if date_from else None,
        "date_to": str(date_to) if date_to else None,
        "adults": adults,
        "children": children,
        "duration_min": duration_min,
        "duration_max": duration_max,
    }

    providers_to_import = []
    if prov_list:
        for p in prov_list:
            if isinstance(p, str):
                norm_p = normalize_provider_name(p)
                if norm_p:
                    try:
                        providers_to_import.append(Provider(norm_p))
                    except ValueError:
                        pass
        if not providers_to_import:
            providers_to_import = list(Provider)
    else:
        providers_to_import = list(Provider)

    imported_providers = []
    for prov in providers_to_import:
        try:
            await run_import(prov, session, filter_params=filter_params)
            imported_providers.append(prov.value)
        except Exception:
            pass

    await session.commit()

    # Query matching offers count post-import to evaluate UI response message
    matched_offers, total_matched = await list_offers(
        session,
        country=cntries,
        region=rgns,
        provider=prov_list,
        departure_city=dep_cities,
        meal_type=meals,
        hotel_stars=stars,
        price_max=price_max,
        date_from=date_from,
        date_to=date_to,
        duration_min=duration_min,
        duration_max=duration_max,
        adults=adults,
        children=children,
    )

    if total_matched == 0:
        # Run QA audit to check if any QA filter contradiction or data issue exists
        qa_report = await run_qa_audit(session)
        qa_cause = None
        for ft in qa_report.get("filter_tests", []):
            if ft.get("status") == "FAILED" and ft.get("explanation"):
                qa_cause = ft.get("explanation")
                break

        if qa_cause:
            msg = f"Import zakończony, ale 0 ofert spełniło wybrane filtry. Wykryta przyczyna QA: {qa_cause}"
        else:
            msg = "Import zakończony, ale żadne oferty nie spełniły wybranych filtrów."

        return {
            "status": "info",
            "imported_providers": imported_providers,
            "count": 0,
            "message": msg,
        }

    return {
        "status": "success",
        "imported_providers": imported_providers,
        "count": total_matched,
        "message": f"Pomyślnie pobrano i zaktualizowano oferty z: {', '.join(imported_providers)} pod zaznaczone filtry!",
    }



@router.get("/{offer_id}", response_model=OfferDetailResponse)
async def get_offer_endpoint(
    offer_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> OfferDetailResponse:
    """Get detailed offer information including price history."""
    offer = await get_offer_detail(offer_id, session)
    if not offer:
        raise HTTPException(status_code=404, detail="Offer not found")

    return OfferDetailResponse(
        **OfferResponse.model_validate(offer).model_dump(),
        first_seen_at=offer.first_seen_at,
        last_seen_at=offer.last_seen_at,
        price_history=[
            PriceHistoryResponse.model_validate(ph) for ph in offer.price_history
        ],
        price_change_pct=compute_price_change_pct(offer),
        days_available=compute_days_available(offer),
    )


@router.get("/{offer_id}/price-history", response_model=list[PriceHistoryResponse])
async def get_offer_price_history_endpoint(
    offer_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> list[PriceHistoryResponse]:
    """Get price change history for a specific offer."""
    history = await get_price_history(offer_id, session)
    if history is None:
        raise HTTPException(status_code=404, detail="Offer not found")

    return [PriceHistoryResponse.model_validate(ph) for ph in history]


@router.delete("/clear-all")
async def clear_all_offers_endpoint(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Clear all offers and historical data from database."""
    from app.services.offer_service import clear_all_offers
    count = await clear_all_offers(session)
    await session.commit()
    return {
        "status": "success",
        "count": count,
        "message": f"Pomyślnie usunięto wszystkie oferty ({count} szt.) z bazy danych.",
    }


@router.delete("/{offer_id}")
async def delete_offer_endpoint(
    offer_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Delete a single offer by ID."""
    from app.services.offer_service import delete_offer
    deleted = await delete_offer(session, offer_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Offer not found")
    await session.commit()
    return {
        "status": "success",
        "message": "Oferta została pomyślnie usunięta z bazy danych.",
    }
