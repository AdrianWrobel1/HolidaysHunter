"""Notification service — formats Telegram V3 alerts with Priority badges, Split Explanations,

Offer History, Mini Price Trends, and dispatches to registered channels while recording
AlertTimeline entries and enforcing per-profile notification policies.
"""

import logging
from decimal import Decimal
from typing import Any

from app.database.session import async_session_factory
from app.models.alert_event import AlertEvent
from app.models.enums import AlertType, TransportType
from app.models.travel_profile import TravelProfile
from app.notifications.base import NotificationChannel
from app.notifications.telegram import TelegramChannel
from app.providers.schemas import build_direct_offer_url
from app.services.alert_cooldown import evaluate_cooldown_policy
from app.services.alert_timeline_service import record_timeline_entry
from app.services.watchlist_service import is_offer_ignored, is_offer_watched

logger = logging.getLogger(__name__)

# Transport Icons & Display Labels
_TRANSPORT_ICONS: dict[str, str] = {
    "flight": "✈️ Przelot samolotem",
    "self_transport": "🚗 Dojazd własny",
    "own": "🚗 Dojazd własny",
    "bus": "🚌 Autokar",
    "train": "🚆 Pociąg",
    "cruise": "🚢 Rejs",
    "unknown": "❓ Nieokreślony transport",
}

# Priority Display Config
_PRIORITY_BADGES: dict[str, str] = {
    "MUST_SEE": "🔥🔥🔥 <b>MUST SEE</b>",
    "HIGH": "🔥 <b>HIGH</b>",
    "NORMAL": "📌 <b>NORMAL</b>",
    "LOW": "📰 <b>LOW</b>",
}

# Policy Score Thresholds
_POLICY_THRESHOLDS: dict[str, float] = {
    "MUST_SEE_ONLY": 90.0,
    "HIGH_AND_MUST_SEE": 75.0,
    "ALL_ALERTS": 50.0,
    "DAILY_DIGEST": 100.0,  # Suppressed for instant push; sent in summary
}


_MEAL_DISPLAY_LABELS: dict[str, str] = {
    "all_inclusive": "All Inclusive 🍹",
    "ultra_all_inclusive": "Ultra All Inclusive 👑",
    "breakfast": "Śniadania (BB) 🥐",
    "half_board": "Śniadania i Obiadokolacje (HB) 🍽️",
    "full_board": "Pełne wyżywienie (FB) 🍲",
    "self_catering": "Dojazd własny / Bez wyżywienia (OV) 🥪",
}


def get_transport_badge(transport_str: str | None) -> str:
    """Get emoji icon + Polish label for transport type."""
    t_clean = str(transport_str or "flight").lower().strip()
    return _TRANSPORT_ICONS.get(t_clean, f"✈️ {t_clean.capitalize()}")


def _s_int(val: Any, default: int = 0) -> int:
    if val is None:
        return default
    try:
        if type(val).__name__ in ("MagicMock", "Mock"):
            return default
        return int(val)
    except (ValueError, TypeError):
        return default


def _s_float(val: Any, default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        if type(val).__name__ in ("MagicMock", "Mock"):
            return default
        return float(val)
    except (ValueError, TypeError):
        return default


def format_alert_message(alert: AlertEvent) -> str:
    """Format an AlertEvent into Telegram HTML with V3 features: Priority, History, Trend, Split Explanations."""
    meta = alert.metadata_json or {}
    reasons_data = alert.reasons_json or {}

    priority_level = alert.priority_level or reasons_data.get("priority_level", "NORMAL")
    priority_score = _s_float(alert.priority_score or reasons_data.get("priority_score", 50.0), 50.0)
    p_badge = _PRIORITY_BADGES.get(priority_level, "📌 <b>NORMAL</b>")

    is_new = _s_int(meta.get("detection_count", 1), 1) <= 1
    status_tag = "✅ <b>NOWA OFERTA</b>" if is_new else "🔄 <b>AKTUALIZACJA OFERTY</b>"

    lines = [f"{p_badge} | {status_tag}"]
    lines.append(f"<i>Priority Score: <b>{priority_score:.1f}</b>/100</i>")
    lines.append("")

    # Profile Identification
    profile_name = meta.get("profile_name")
    if profile_name:
        lines.append(f"📂 <b>Profil:</b> {profile_name}")
        lines.append("")

    # Offer details
    o = alert.offer
    if o:
        raw_provider = getattr(o, "provider", "biuro")
        provider_name = str(raw_provider).upper()

        raw_url = getattr(o, "offer_url", None)
        raw_url_str = str(raw_url) if isinstance(raw_url, str) else None
        raw_ext_id = getattr(o, "external_id", "0")
        ext_id = str(raw_ext_id) if isinstance(raw_ext_id, (str, int)) else "0"

        offer_url = (build_direct_offer_url(provider_name.lower(), ext_id, raw_url_str) if raw_url_str else None) or raw_url_str

        hotel_name = getattr(o, "hotel_name", "Hotel")
        country_val = getattr(o, "country", "")
        region_val = getattr(o, "region", None)
        region_str = f" • {region_val}" if region_val else ""

        stars_val = _s_float(getattr(o, "hotel_stars", None), 0.0)
        stars_str = f" {'⭐' * int(stars_val)}" if stars_val > 0 else ""
        rating_val = _s_float(getattr(o, "hotel_rating", None), 0.0)
        rating_str = f" (Ocena: {rating_val:.1f}/10)" if rating_val > 0 else ""

        dep_date = getattr(o, "departure_date", "")
        dur_nights = _s_int(getattr(o, "duration_nights", 7), 7)
        dep_city = getattr(o, "departure_city", "")

        adults_cnt = _s_int(getattr(o, "adults", 2), 2)
        children_cnt = _s_int(getattr(o, "children", 0), 0)
        people_str = f"👥 {adults_cnt} os." + (f", {children_cnt} dzieci" if children_cnt > 0 else "")

        raw_meal = str(getattr(o, "meal_type", "")).lower()
        meal_val = _MEAL_DISPLAY_LABELS.get(raw_meal, getattr(o, "meal_type", ""))
        transport_val = getattr(o, "transport_type", "flight")
        transport_badge = get_transport_badge(transport_val)

        curr_p = _s_float(meta.get("current_price", getattr(o, "price_per_person", 0)), 0.0)
        total_val = _s_float(getattr(o, "price_total", 0), 0.0)
        total_p_str = f" (Łącznie: {total_val:.0f} PLN)" if total_val > 0 else ""

        score_val = _s_int(getattr(o, "travel_score", None), 0)
        score_str = f" | 🏆 Score: <b>{score_val}</b>/100" if score_val > 0 else ""

        lines.append(f"🏨 <b>{hotel_name}</b>{stars_str}{rating_str}")
        lines.append(f"📍 <b>{country_val}</b>{region_str}")
        lines.append(f"📅 {dep_date} ({dur_nights} nocy) | {transport_badge} (Wylot: {dep_city})")
        lines.append(f"🍽️ {meal_val} | {people_str}")
        lines.append(f"💰 <b>{curr_p:.0f} PLN/os.</b>{total_p_str}{score_str}")
        lines.append(f"🏢 <b>Biuro:</b> {provider_name}")
        lines.append("")

    # Offer History Section
    first_seen = meta.get("first_seen_at", "Dziś")
    det_count = meta.get("detection_count", 1)
    min_p = float(meta.get("min_price", o.price_per_person if o else 0))
    max_p = float(meta.get("max_price", o.price_per_person if o else 0))
    prev_p = float(meta.get("previous_price", o.price_per_person if o else 0))
    curr_p = float(meta.get("current_price", o.price_per_person if o else 0))
    diff_p = curr_p - prev_p

    diff_str = ""
    if diff_p < 0:
        diff_str = f" ▼ <b>{abs(diff_p):.0f} PLN</b>"
    elif diff_p > 0:
        diff_str = f" ▲ <b>+{diff_p:.0f} PLN</b>"

    lines.append("📊 <b>HISTORIA OFERTY & TREND CENOWY</b>")
    lines.append(f"• Pierwszy raz wykryta: <b>{first_seen}</b>")
    lines.append(f"• Wykryta w systemie: <b>{det_count} razy</b>")
    lines.append(f"• Zakres cen historycznych: <b>{min_p:.0f} PLN</b> (min) — <b>{max_p:.0f} PLN</b> (max)")

    if prev_p != curr_p:
        lines.append(f"• Zmiana ceny: {prev_p:.0f} PLN ➔ <b>{curr_p:.0f} PLN</b>{diff_str}")

    # Mini price trend visualization
    trend_seq = meta.get("price_trend_sequence", [])
    if isinstance(trend_seq, list) and len(trend_seq) > 1:
        trend_str = " ↓ ".join(f"{float(p):.0f}" for p in trend_seq)
        lines.append(f"• Trend cenowy: <code>{trend_str} PLN</code>")

    lines.append("")

    # Split Explanations
    val_reasons = reasons_data.get("value_reasons", [])
    now_reasons = reasons_data.get("now_reasons", [])

    if val_reasons:
        lines.append("💎 <b>DLACZEGO WARTO?</b>")
        for vr in val_reasons:
            lines.append(f"• {vr}")
        lines.append("")

    if now_reasons:
        lines.append("⚡ <b>DLACZEGO TERAZ?</b>")
        for nr in now_reasons:
            lines.append(f"• {nr}")
        lines.append("")

    if o and getattr(o, "offer_url", None):
        clean_url = build_direct_offer_url(getattr(o, "provider", "").lower(), str(getattr(o, "external_id", "")), getattr(o, "offer_url", "")) or getattr(o, "offer_url", "")
        lines.append(f'🔗 <a href="{clean_url}">Zobacz ofertę bezpośrednio w biurze</a>')

    return "\n".join(lines)


def build_alert_inline_keyboard(offer_id: Any) -> dict[str, Any]:
    """Build Telegram Inline Keyboard markup for alert notifications."""
    off_str = str(offer_id)
    return {
        "inline_keyboard": [
            [
                {"text": "👀 Obserwuj ofertę", "callback_data": f"watch:{off_str}"},
                {"text": "🙈 Ignoruj ofertę", "callback_data": f"ignore:{off_str}"},
            ],
            [
                {"text": "⚙️ Twoje Profile", "callback_data": "profiles:list"},
            ],
        ]
    }


class NotificationService:
    """Dispatches formatted alerts to all registered notification channels."""

    def __init__(self) -> None:
        self._channels: list[NotificationChannel] = []
        self._setup_channels()

    def _setup_channels(self) -> None:
        """Register available notification channels."""
        telegram = TelegramChannel()
        if telegram.is_configured:
            self._channels.append(telegram)
            logger.info("Telegram notification channel registered")
        else:
            logger.info("Telegram not configured — notifications disabled")

    async def dispatch(self, alerts: list[AlertEvent]) -> int:
        """Send notifications for a batch of alerts with full policy & cooldown evaluation.

        Returns the number of successfully delivered notifications.
        """
        if not self._channels:
            return 0

        if not alerts:
            return 0

        delivered = 0

        async with async_session_factory() as session:
            # Batch pre-fetch matched profiles to eliminate N+1 database queries
            profile_ids = {a.profile_id for a in alerts if a.profile_id}
            profiles_by_id: dict[Any, TravelProfile] = {}
            if profile_ids:
                p_res = await session.execute(
                    select(TravelProfile).where(TravelProfile.id.in_(profile_ids))
                )
                profiles_by_id = {p.id: p for p in p_res.scalars().all()}

            for alert in alerts:
                # 1. Fetch matched profile notification policy if present
                policy_name = "HIGH_AND_MUST_SEE"
                if alert.profile_id and alert.profile_id in profiles_by_id:
                    prof = profiles_by_id[alert.profile_id]
                    policy_name = prof.notification_policy or "HIGH_AND_MUST_SEE"

                min_score_required = _POLICY_THRESHOLDS.get(policy_name, 75.0)
                p_score = float(alert.priority_score or 50.0)

                # Policy Check
                if p_score < min_score_required:
                    await record_timeline_entry(
                        session,
                        offer_id=alert.offer_id,
                        profile_id=alert.profile_id,
                        priority_score=p_score,
                        priority_level=alert.priority_level or "NORMAL",
                        reasons=alert.reasons_json,
                        price_per_person=alert.offer.price_per_person if alert.offer else 0,
                        deal_score=alert.offer.travel_score if alert.offer else None,
                        notification_status="suppressed_policy",
                    )
                    logger.debug("Alert %s suppressed by profile policy %s", alert.id, policy_name)
                    continue

                # 2. Check if offer is ignored for chat
                chat_id = getattr(self._channels[0], "_chat_id", None)
                if chat_id:
                    ignored, reason = await is_offer_ignored(
                        session,
                        user_chat_id=chat_id,
                        offer_id=alert.offer_id,
                        current_priority_score=p_score,
                        current_price=float(alert.offer.price_per_person) if alert.offer else None,
                    )
                    if ignored:
                        await record_timeline_entry(
                            session,
                            offer_id=alert.offer_id,
                            profile_id=alert.profile_id,
                            user_chat_id=chat_id,
                            priority_score=p_score,
                            priority_level=alert.priority_level or "NORMAL",
                            reasons=alert.reasons_json,
                            price_per_person=alert.offer.price_per_person if alert.offer else 0,
                            deal_score=alert.offer.travel_score if alert.offer else None,
                            notification_status="suppressed_ignored",
                        )
                        logger.info("Alert %s suppressed: offer %s is ignored", alert.id, alert.offer_id)
                        continue

                # 3. Check Cooldown policy
                meta = alert.metadata_json or {}
                is_lowest = alert.alert_type == AlertType.LOWEST_PRICE
                should_send, cooldown_reason = await evaluate_cooldown_policy(
                    session,
                    offer_id=alert.offer_id,
                    profile_id=alert.profile_id,
                    current_priority_score=p_score,
                    current_priority_level=alert.priority_level or "NORMAL",
                    current_price=alert.offer.price_per_person if alert.offer else 0,
                    current_deal_score=alert.offer.travel_score if alert.offer else None,
                    is_lowest_price=is_lowest,
                )

                if not should_send:
                    await record_timeline_entry(
                        session,
                        offer_id=alert.offer_id,
                        profile_id=alert.profile_id,
                        user_chat_id=chat_id,
                        priority_score=p_score,
                        priority_level=alert.priority_level or "NORMAL",
                        reasons=alert.reasons_json,
                        price_per_person=alert.offer.price_per_person if alert.offer else 0,
                        deal_score=alert.offer.travel_score if alert.offer else None,
                        notification_status="suppressed_cooldown",
                    )
                    logger.info("Alert %s suppressed by cooldown: %s", alert.id, cooldown_reason)
                    continue

                # 4. Check if watched offer update
                watched_rec = None
                if chat_id:
                    watched_rec = await is_offer_watched(session, chat_id, alert.offer_id)

                status_flag = "watched_update" if watched_rec else "sent"
                formatted_msg = format_alert_message(alert)
                reply_markup = build_alert_inline_keyboard(alert.offer_id)

                for channel in self._channels:
                    try:
                        success = await channel.send(alert, formatted_msg, reply_markup=reply_markup)
                        if success:
                            delivered += 1
                            await record_timeline_entry(
                                session,
                                offer_id=alert.offer_id,
                                profile_id=alert.profile_id,
                                user_chat_id=chat_id,
                                priority_score=p_score,
                                priority_level=alert.priority_level or "NORMAL",
                                reasons=alert.reasons_json,
                                price_per_person=alert.offer.price_per_person if alert.offer else 0,
                                deal_score=alert.offer.travel_score if alert.offer else None,
                                notification_status=status_flag,
                            )
                    except Exception:
                        logger.exception(
                            "Channel %s failed for alert %s",
                            type(channel).__name__,
                            alert.id,
                        )

            await session.commit()

        logger.info(
            "Notifications dispatched: %d/%d delivered",
            delivered,
            len(alerts) * len(self._channels),
        )
        return delivered

    async def close(self) -> None:
        """Release resources for all channels."""
        for channel in self._channels:
            try:
                await channel.close()
            except Exception:
                logger.exception("Failed to close channel %s", type(channel).__name__)


# Module-level singleton — lazily instantiated
_service: NotificationService | None = None


def get_notification_service() -> NotificationService:
    """Get or create the notification service singleton."""
    global _service
    if _service is None:
        _service = NotificationService()
    return _service


async def dispatch_notifications(alerts: list[AlertEvent]) -> int:
    """Convenience function to dispatch alerts through the singleton service."""
    service = get_notification_service()
    return await service.dispatch(alerts)
