import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Provider, TransportType
from app.models.offer import Offer
from app.models.price_history import PriceHistory
from app.notifications.service import dispatch_notifications
from app.providers.registry import get_provider_entry
from app.providers.schemas import NormalizedOffer
from app.services.alert_service import evaluate_alerts
from app.services.qa_service import run_qa_audit, store_raw_payload
from app.services.scoring_service import recalculate_scores

logger = logging.getLogger(__name__)


async def run_import(
    provider: Provider,
    session: AsyncSession,
    filter_params: dict | None = None,
) -> None:
    """Execute the full import pipeline for a single provider.

    Pipeline steps (per architecture doc):
    1. Fetch raw offers from provider API
    2. Normalize each offer to unified schema
    3. Upsert into database (insert new, update existing)
    4. Record price history on price changes
    5. Mark disappeared offers as unavailable
    """
    entry = get_provider_entry(provider)
    importer = entry.create_provider()
    normalizer = entry.create_normalizer()

    logger.info(
        "[import_service] Import START — provider=%s, filter_params=%s",
        provider.value, filter_params,
    )

    try:
        if hasattr(importer.fetch_offers, "__code__") and "filter_params" in importer.fetch_offers.__code__.co_varnames:
            raw_offers = await importer.fetch_offers(filter_params=filter_params)
        else:
            raw_offers = await importer.fetch_offers()
    except Exception:
        logger.exception("[import_service] Fetch FAILED for %s", provider.value)
        return
    finally:
        if hasattr(importer, "close"):
            await importer.close()

    logger.info("[import_service] %s: fetched %d raw offers from provider", provider.value, len(raw_offers))

    seen_offer_ids: set[str] = set()
    new_offers: list[Offer] = []
    updated_offers: list[Offer] = []
    skipped_count = 0
    skipped_transport_count = 0
    normalized_count = 0

    from app.services.qa_service import store_import_audit_record

    for raw in raw_offers:
        api_reg = raw.get("region") or raw.get("regionName") or raw.get("region_name") or "NONE"
        ext_id = raw.get("external_id") or raw.get("offerId") or raw.get("id") or raw.get("offerCode") or "UNKNOWN"
        hotel_name = raw.get("hotel_name") or raw.get("hotelName") or raw.get("name") or raw.get("title") or "UNKNOWN"

        normalized = normalizer.normalize(raw)
        if normalized is None:
            skipped_count += 1
            store_import_audit_record({
                "external_id": str(ext_id),
                "hotel": str(hotel_name),
                "api_region": str(api_reg),
                "normalized_region": "NONE",
                "db_region": "NONE",
                "status": "skipped",
                "reason": "Odrzucono podczas normalizacji: brakujące wymagane pola lub niepoprawny format daty/ceny",
            })
            continue

        # --- Transport filter: accept all valid TransportTypes ---
        if not isinstance(normalized.transport_type, TransportType):
            logger.debug(
                "[import_service] %s: unhandled transport_type=%s for offer %s",
                provider.value, normalized.transport_type, normalized.external_id,
            )

        store_raw_payload(provider.value, normalized.external_id, raw)

        normalized_count += 1
        seen_offer_ids.add(normalized.external_id)

        existing = await _find_existing_offer(session, normalized)

        if existing is None:
            offer = _create_offer(session, normalized)
            new_offers.append(offer)
            store_import_audit_record({
                "external_id": normalized.external_id,
                "hotel": normalized.hotel_name,
                "api_region": str(api_reg),
                "normalized_region": normalized.region or "NONE",
                "db_region": normalized.region or "NONE",
                "status": "saved",
                "reason": "Pomyślnie utworzono nowy rekord w bazie danych",
            })
        else:
            price_changed = _update_offer(existing, normalized)
            if price_changed:
                _record_price_change(session, existing)
                updated_offers.append(existing)
            status_val = "updated" if price_changed else "duplicate"
            reason_val = (
                "Rekord już istniał w bazie — zaktualizowano cenę i czas ostatniego widzenia (deduplikacja tożsamości)"
                if price_changed else
                "Identyczny rekord już istnieje w bazie — zaktualizowano czas widzenia (deduplikacja)"
            )
            store_import_audit_record({
                "external_id": normalized.external_id,
                "hotel": normalized.hotel_name,
                "api_region": str(api_reg),
                "normalized_region": normalized.region or "NONE",
                "db_region": existing.region or "NONE",
                "status": status_val,
                "reason": reason_val,
            })

    logger.info(
        "[import_service] %s: normalized=%d, skipped=%d, skipped_transport=%d, new=%d, updated=%d — seen_ids count=%d",
        provider.value, normalized_count, skipped_count, skipped_transport_count,
        len(new_offers), len(updated_offers), len(seen_offer_ids),
    )

    reappeared_offers = await _mark_unavailable(
        session, provider, seen_offer_ids, filter_params=filter_params
    )

    await session.flush()

    # --- Post-import pipeline: scoring, alerts, notifications ---
    all_touched = new_offers + updated_offers + reappeared_offers
    if all_touched:
        await recalculate_scores(all_touched, session)
        alert_events = await evaluate_alerts(
            new_offers, updated_offers, reappeared_offers, session
        )
        await session.flush()

        if alert_events:
            try:
                await dispatch_notifications(alert_events)
            except Exception:
                logger.exception("%s: notification dispatch failed", provider.value)

    # --- Run Offer QA Validation & Filter Audit ---
    try:
        await run_qa_audit(session)
    except Exception:
        logger.exception("[import_service] %s: QA audit failed", provider.value)

    logger.info(
        "[import_service] %s import DONE: new=%d, updated=%d, reappeared=%d, skipped=%d, skipped_transport=%d",
        provider.value,
        len(new_offers),
        len(updated_offers),
        len(reappeared_offers),
        skipped_count,
        skipped_transport_count,
    )


async def _find_existing_offer(
    session: AsyncSession, normalized: NormalizedOffer
) -> Offer | None:
    """Find an existing offer matching the unique identity constraint."""
    stmt = select(Offer).where(
        Offer.provider == normalized.provider.value,
        Offer.external_id == normalized.external_id,
        Offer.departure_date == normalized.departure_date,
        Offer.departure_city == normalized.departure_city,
        Offer.adults == normalized.adults,
        Offer.children == normalized.children,
        Offer.transport_type == normalized.transport_type.value,
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def _create_offer(session: AsyncSession, normalized: NormalizedOffer) -> Offer:
    """Insert a new offer and its initial price history record."""
    now = datetime.now(timezone.utc)
    offer = Offer(
        external_id=normalized.external_id,
        provider=normalized.provider.value,
        title=normalized.title,
        country=normalized.country,
        region=normalized.region,
        city=normalized.city,
        hotel_name=normalized.hotel_name,
        hotel_stars=normalized.hotel_stars,
        hotel_rating=normalized.hotel_rating,
        departure_date=normalized.departure_date,
        return_date=normalized.return_date,
        duration_nights=normalized.duration_nights,
        departure_city=normalized.departure_city,
        adults=normalized.adults,
        children=normalized.children,
        meal_type=normalized.meal_type.value,
        transport_type=normalized.transport_type.value,
        price_total=normalized.price_total,
        price_per_person=normalized.price_per_person,
        currency=normalized.currency,
        offer_url=normalized.offer_url,
        image_url=normalized.image_url,
        is_available=True,
        first_seen_at=now,
        last_seen_at=now,
    )
    session.add(offer)

    price_record = PriceHistory(
        offer=offer,
        price_total=normalized.price_total,
        price_per_person=normalized.price_per_person,
    )
    session.add(price_record)

    return offer


def _update_offer(existing: Offer, normalized: NormalizedOffer) -> bool:
    """Update an existing offer with fresh data. Returns True if price changed."""
    now = datetime.now(timezone.utc)

    price_changed = (
        existing.price_total != normalized.price_total
        or existing.price_per_person != normalized.price_per_person
    )

    existing.title = normalized.title
    existing.country = normalized.country
    existing.region = normalized.region
    existing.city = normalized.city
    existing.hotel_name = normalized.hotel_name
    existing.hotel_stars = normalized.hotel_stars
    existing.hotel_rating = normalized.hotel_rating
    existing.return_date = normalized.return_date
    existing.duration_nights = normalized.duration_nights
    existing.meal_type = normalized.meal_type.value
    existing.transport_type = normalized.transport_type.value
    existing.price_total = normalized.price_total
    existing.price_per_person = normalized.price_per_person
    existing.currency = normalized.currency
    existing.offer_url = normalized.offer_url
    existing.image_url = normalized.image_url
    existing.is_available = True
    existing.last_seen_at = now

    return price_changed


def _record_price_change(session: AsyncSession, offer: Offer) -> None:
    """Record a new price history entry after a price change."""
    record = PriceHistory(
        offer=offer,
        price_total=offer.price_total,
        price_per_person=offer.price_per_person,
    )
    session.add(record)


async def _mark_unavailable(
    session: AsyncSession,
    provider: Provider,
    seen_ids: set[str],
    filter_params: dict | None = None,
) -> list[Offer]:
    """Mark offers not present in this import as unavailable within the import scope.

    Also detects offers that reappeared (were unavailable but are now seen).
    Returns list of reappeared offers.
    """
    reappeared: list[Offer] = []

    if not seen_ids:
        logger.warning("[%s] No offers seen in this import, skipping availability update.", provider.value)
        return reappeared

    # Find reappeared offers (were unavailable, now seen again)
    reappear_stmt = select(Offer).where(
        Offer.provider == provider.value,
        Offer.is_available.is_(False),
        Offer.external_id.in_(seen_ids),
    )
    reappear_result = await session.execute(reappear_stmt)
    for offer in reappear_result.scalars().all():
        offer.is_available = True
        reappeared.append(offer)

    if reappeared:
        logger.info("[%s] %d offers marked as available again.", provider.value, len(reappeared))

    # Mark disappeared offers ONLY within the target filter scope
    from app.core.countries import normalize_country_name
    stmt = select(Offer).where(
        Offer.provider == provider.value,
        Offer.is_available.is_(True),
        Offer.external_id.notin_(seen_ids),
    )

    scope_description = "all"
    if filter_params and filter_params.get("country"):
        country_val = filter_params["country"]
        if isinstance(country_val, list) and country_val:
            canonical_countries = [normalize_country_name(c) for c in country_val]
            stmt = stmt.where(Offer.country.in_(canonical_countries))
            scope_description = f"countries={canonical_countries}"
        elif isinstance(country_val, str) and country_val:
            canonical_country = normalize_country_name(country_val)
            stmt = stmt.where(Offer.country == canonical_country)
            scope_description = f"country={canonical_country}"

    logger.debug("[%s] Running unavailability check with scope: %s", provider.value, scope_description)
    
    result = await session.execute(stmt)
    disappeared = result.scalars().all()

    for offer in disappeared:
        offer.is_available = False

    if disappeared:
        logger.info(
            "[%s] Marked %d offers as unavailable (Scope: %s)",
            provider.value,
            len(disappeared),
            scope_description,
        )

    return reappeared
