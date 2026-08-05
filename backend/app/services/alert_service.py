# -*- coding: utf-8 -*-
"""Alert Engine - detects noteworthy events and creates AlertEvent records.

The engine runs after each import and evaluates every new or updated offer
against alert rules. It creates AlertEvent rows but does NOT send
notifications - that responsibility belongs to the Notification Service.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert_event import AlertEvent
from app.models.enums import AlertType
from app.models.offer import Offer
from app.models.price_history import PriceHistory
from app.models.travel_profile import TravelProfile
from app.services.scoring_service import offer_matches_profile

logger = logging.getLogger(__name__)

# Thresholds
PRICE_DROP_THRESHOLD_PCT = 5.0
HIGH_SCORE_THRESHOLD = 75
LOWEST_PRICE_LOOKBACK_DAYS = 30


async def evaluate_alerts(
    new_offers: list[Offer],
    updated_offers: list[Offer],
    reappeared_offers: list[Offer],
    session: AsyncSession,
) -> list[AlertEvent]:
    """Evaluate all alert rules for offers from a single import run.

    Returns a list of created AlertEvent records (already added to session).
    """
    profiles_result = await session.execute(
        select(TravelProfile).where(TravelProfile.is_active.is_(True))
    )
    profiles = list(profiles_result.scalars().all())

    events: list[AlertEvent] = []

    # --- New offers matching profiles ---
    for offer in new_offers:
        for profile in profiles:
            if offer_matches_profile(offer, profile):
                event = _create_alert(
                    offer=offer,
                    profile=profile,
                    alert_type=AlertType.NEW_MATCH,
                    message=(
                        f"Nowa oferta pasujaca do profilu [{profile.name}]: "
                        f"{offer.hotel_name}, {offer.country} "
                        f"- {offer.price_per_person} PLN/os."
                    ),
                    metadata={
                        "profile_name": profile.name,
                        "price_per_person": str(offer.price_per_person),
                    },
                )
                session.add(event)
                events.append(event)

    # --- Price drops on existing offers ---
    for offer in updated_offers:
        price_event = _check_price_drop(offer, profiles)
        if price_event:
            session.add(price_event)
            events.append(price_event)

        lowest_event = _check_lowest_price(offer)
        if lowest_event:
            session.add(lowest_event)
            events.append(lowest_event)

    # --- High Travel Score ---
    for offer in new_offers + updated_offers:
        if offer.travel_score is not None and offer.travel_score >= HIGH_SCORE_THRESHOLD:
            event = _create_alert(
                offer=offer,
                profile=None,
                alert_type=AlertType.HIGH_SCORE,
                message=(
                    f"Wysoki Travel Score ({offer.travel_score}/100): "
                    f"{offer.hotel_name}, {offer.country} "
                    f"- {offer.price_per_person} PLN/os."
                ),
                metadata={"travel_score": offer.travel_score},
            )
            session.add(event)
            events.append(event)

    # --- Reappeared offers ---
    for offer in reappeared_offers:
        for profile in profiles:
            if offer_matches_profile(offer, profile):
                event = _create_alert(
                    offer=offer,
                    profile=profile,
                    alert_type=AlertType.REAPPEARED,
                    message=(
                        f"Oferta ponownie dostepna: {offer.hotel_name}, "
                        f"{offer.country} - {offer.price_per_person} PLN/os."
                    ),
                    metadata={
                        "profile_name": profile.name,
                        "price_per_person": str(offer.price_per_person),
                    },
                )
                session.add(event)
                events.append(event)
                break

    if events:
        logger.info("Alert engine generated %d events", len(events))

    return events


def _check_price_drop(
    offer: Offer,
    profiles: list[TravelProfile],
) -> AlertEvent | None:
    """Check if the most recent price change is a significant drop."""
    if not offer.price_history or len(offer.price_history) < 2:
        return None

    sorted_history = sorted(offer.price_history, key=lambda ph: ph.recorded_at)
    previous_price = sorted_history[-2].price_per_person
    current_price = sorted_history[-1].price_per_person

    if previous_price <= 0:
        return None

    change_pct = float((current_price - previous_price) / previous_price * 100)

    if change_pct >= -PRICE_DROP_THRESHOLD_PCT:
        return None

    matching_profile = None
    for profile in profiles:
        if offer_matches_profile(offer, profile):
            matching_profile = profile
            break

    return _create_alert(
        offer=offer,
        profile=matching_profile,
        alert_type=AlertType.PRICE_DROP,
        message=(
            f"Spadek ceny o {abs(change_pct):.1f}%: {offer.hotel_name}, "
            f"{offer.country} - {previous_price} -> {current_price} PLN/os."
        ),
        metadata={
            "previous_price": str(previous_price),
            "current_price": str(current_price),
            "change_pct": round(change_pct, 1),
        },
    )


def _check_lowest_price(offer: Offer) -> AlertEvent | None:
    """Check if current price is the lowest in the lookback window."""
    if not offer.price_history or len(offer.price_history) < 3:
        return None

    sorted_history = sorted(offer.price_history, key=lambda ph: ph.recorded_at)
    current_price = sorted_history[-1].price_per_person

    now = datetime.now(timezone.utc)
    recent_entries = []
    for ph in sorted_history[:-1]:
        recorded = ph.recorded_at
        if recorded.tzinfo is None:
            recorded = recorded.replace(tzinfo=timezone.utc)
        if (now - recorded).days <= LOWEST_PRICE_LOOKBACK_DAYS:
            recent_entries.append(ph)

    if not recent_entries:
        return None

    historical_min = min(ph.price_per_person for ph in recent_entries)

    if current_price < historical_min:
        return _create_alert(
            offer=offer,
            profile=None,
            alert_type=AlertType.LOWEST_PRICE,
            message=(
                f"Najnizsza cena od {LOWEST_PRICE_LOOKBACK_DAYS} dni: "
                f"{offer.hotel_name}, {offer.country} "
                f"- {current_price} PLN/os."
            ),
            metadata={
                "current_price": str(current_price),
                "previous_min": str(historical_min),
                "lookback_days": LOWEST_PRICE_LOOKBACK_DAYS,
            },
        )

    return None


def _create_alert(
    *,
    offer: Offer,
    profile: TravelProfile | None,
    alert_type: AlertType,
    message: str,
    metadata: dict | None = None,
) -> AlertEvent:
    """Factory for AlertEvent creation."""
    return AlertEvent(
        offer_id=offer.id,
        profile_id=profile.id if profile else None,
        alert_type=alert_type.value,
        message=message,
        metadata_json=metadata,
    )
