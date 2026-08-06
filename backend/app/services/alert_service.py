# -*- coding: utf-8 -*-
"""Alert Engine - detects noteworthy events and creates AlertEvent records.

The engine runs after each import and evaluates every new or updated offer
against alert rules. It calculates priority score/level, populates structured reasons,
and attaches complete offer history metadata for notification dispatch.
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
from app.services.alert_priority import calculate_alert_priority
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
                event = _build_and_create_alert(
                    offer=offer,
                    profile=profile,
                    alert_type=AlertType.NEW_MATCH,
                    message=(
                        f"Nowa oferta pasująca do profilu [{profile.name}]: "
                        f"{offer.hotel_name}, {offer.country} "
                        f"- {offer.price_per_person} PLN/os."
                    ),
                    metadata={"profile_name": profile.name},
                )
                session.add(event)
                events.append(event)

    # --- Price drops & lowest price on existing offers ---
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
            # Check if alert for this high score was already generated
            event = _build_and_create_alert(
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
        matching_profile = None
        for profile in profiles:
            if offer_matches_profile(offer, profile):
                matching_profile = profile
                break

        event = _build_and_create_alert(
            offer=offer,
            profile=matching_profile,
            alert_type=AlertType.REAPPEARED,
            message=(
                f"Oferta ponownie dostępna: {offer.hotel_name}, "
                f"{offer.country} - {offer.price_per_person} PLN/os."
            ),
            metadata={"profile_name": matching_profile.name if matching_profile else None},
        )
        session.add(event)
        events.append(event)

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

    return _build_and_create_alert(
        offer=offer,
        profile=matching_profile,
        alert_type=AlertType.PRICE_DROP,
        message=(
            f"Spadek ceny o {abs(change_pct):.1f}%: {offer.hotel_name}, "
            f"{offer.country} - {previous_price} -> {current_price} PLN/os."
        ),
        previous_price=previous_price,
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
        previous_price = sorted_history[-2].price_per_person if len(sorted_history) >= 2 else None
        return _build_and_create_alert(
            offer=offer,
            profile=None,
            alert_type=AlertType.LOWEST_PRICE,
            message=(
                f"Najniższa cena od {LOWEST_PRICE_LOOKBACK_DAYS} dni: "
                f"{offer.hotel_name}, {offer.country} "
                f"- {current_price} PLN/os."
            ),
            previous_price=previous_price,
            is_lowest_price=True,
            metadata={
                "current_price": str(current_price),
                "previous_min": str(historical_min),
                "lookback_days": LOWEST_PRICE_LOOKBACK_DAYS,
            },
        )

    return None


def _build_and_create_alert(
    *,
    offer: Offer,
    profile: TravelProfile | None,
    alert_type: AlertType,
    message: str,
    previous_price: Decimal | float | None = None,
    is_lowest_price: bool = False,
    metadata: dict | None = None,
) -> AlertEvent:
    """Factory for AlertEvent creation with Priority Engine calculation and history stats."""
    priority_res = calculate_alert_priority(
        offer=offer,
        alert_type=alert_type,
        profile=profile,
        previous_price=previous_price,
        is_lowest_price=is_lowest_price,
    )

    # Compute full price history stats
    history_prices = []
    if offer.price_history:
        sorted_h = sorted(offer.price_history, key=lambda ph: ph.recorded_at)
        history_prices = [float(ph.price_per_person) for ph in sorted_h]
    else:
        history_prices = [float(offer.price_per_person)]

    min_p = min(history_prices) if history_prices else float(offer.price_per_person)
    max_p = max(history_prices) if history_prices else float(offer.price_per_person)
    curr_p = float(offer.price_per_person)
    prev_p = float(previous_price) if previous_price is not None else (history_prices[-2] if len(history_prices) >= 2 else curr_p)
    diff_p = curr_p - prev_p

    first_seen_str = offer.first_seen_at.strftime("%Y-%m-%d %H:%M") if offer.first_seen_at else datetime.now().strftime("%Y-%m-%d %H:%M")

    meta = metadata or {}
    meta.update({
        "first_seen_at": first_seen_str,
        "detection_count": len(history_prices),
        "min_price": min_p,
        "max_price": max_p,
        "previous_price": prev_p,
        "current_price": curr_p,
        "price_change_amount": diff_p,
        "price_trend_sequence": history_prices[-5:],  # Last 5 prices
        "profile_name": profile.name if profile else meta.get("profile_name"),
    })

    return AlertEvent(
        offer_id=offer.id,
        profile_id=profile.id if profile else None,
        alert_type=alert_type.value if hasattr(alert_type, "value") else str(alert_type),
        message=message,
        priority_score=priority_res.priority_score,
        priority_level=priority_res.priority_level.value,
        reasons_json=priority_res.to_dict(),
        metadata_json=meta,
    )
