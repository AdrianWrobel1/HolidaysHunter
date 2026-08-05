"""Notification service — formats alerts and dispatches to channels.

This is the orchestrator. It takes raw AlertEvent objects, formats them
into human-readable messages, and sends them through registered channels.
"""

import logging
from decimal import Decimal

from app.models.alert_event import AlertEvent
from app.models.enums import AlertType
from app.notifications.base import NotificationChannel
from app.notifications.telegram import TelegramChannel

logger = logging.getLogger(__name__)

# Alert type display config
_ALERT_EMOJI: dict[str, str] = {
    AlertType.NEW_MATCH: "\U0001f31f",      # star
    AlertType.PRICE_DROP: "\U0001f4b0",      # money bag
    AlertType.LOWEST_PRICE: "\U0001f525",    # fire
    AlertType.HIGH_SCORE: "\U0001f3c6",      # trophy
    AlertType.REAPPEARED: "\U0001f504",      # arrows cycle
}

_ALERT_TITLE: dict[str, str] = {
    AlertType.NEW_MATCH: "Nowa oferta",
    AlertType.PRICE_DROP: "Spadek ceny",
    AlertType.LOWEST_PRICE: "Najnizsza cena",
    AlertType.HIGH_SCORE: "Wysoki Travel Score",
    AlertType.REAPPEARED: "Oferta powrocila",
}


from app.providers.schemas import build_direct_offer_url

def format_alert_message(alert: AlertEvent) -> str:
    """Format an AlertEvent into an HTML message for Telegram."""
    emoji = _ALERT_EMOJI.get(alert.alert_type, "\u2139\ufe0f")
    title = _ALERT_TITLE.get(alert.alert_type, "Alert")

    lines = [f"{emoji} <b>{title}</b>"]
    lines.append("")
    lines.append(alert.message)

    # Add metadata details
    meta = alert.metadata_json or {}

    if alert.alert_type == AlertType.PRICE_DROP:
        prev = meta.get("previous_price", "")
        curr = meta.get("current_price", "")
        pct = meta.get("change_pct", "")
        if prev and curr:
            lines.append(f"\n📉 <b>Cena zmiana:</b> {prev} -> {curr} PLN/os. ({pct}%)")

    if alert.alert_type == AlertType.HIGH_SCORE:
        score = meta.get("travel_score", "")
        if score:
            lines.append(f"\n🏆 <b>Travel Score:</b> {score}/100")

    if alert.alert_type == AlertType.LOWEST_PRICE:
        lookback = meta.get("lookback_days", 30)
        prev_min = meta.get("previous_min", "")
        if prev_min:
            lines.append(
                f"\n🔥 <b>Poprzednie minimum:</b> {prev_min} PLN/os. "
                f"(ostatnie {lookback} dni)"
            )

    # Add rich offer details & direct link
    if alert.offer:
        o = alert.offer
        raw_provider = getattr(o, "provider", None)
        provider_name = str(raw_provider).upper() if isinstance(raw_provider, str) else "BIURO"
        
        raw_url = getattr(o, "offer_url", None)
        raw_url_str = str(raw_url) if isinstance(raw_url, str) else None
        
        raw_ext_id = getattr(o, "external_id", None)
        ext_id = str(raw_ext_id) if isinstance(raw_ext_id, (str, int)) else "0"
        
        # Build absolute URL using schema helper
        offer_url = (build_direct_offer_url(provider_name.lower(), ext_id, raw_url_str) if raw_url_str else None) or raw_url_str

        hotel_name = getattr(o, "hotel_name", None)
        hotel_name_str = str(hotel_name) if isinstance(hotel_name, str) else None
        
        country_val = getattr(o, "country", None)
        country_str = str(country_val) if isinstance(country_val, str) else None

        stars_val = getattr(o, "hotel_stars", None)
        stars_str = f" {'⭐' * int(stars_val)}" if isinstance(stars_val, (int, float)) and stars_val > 0 else ""

        rating_val = getattr(o, "hotel_rating", None)
        rating_str = f" (Ocena: {rating_val}/10)" if isinstance(rating_val, (int, float)) else ""

        region_val = getattr(o, "region", None)
        region_str = f" • {region_val}" if isinstance(region_val, str) else ""
        
        adults_val = getattr(o, "adults", None)
        adults_count = adults_val if isinstance(adults_val, int) else 2
        children_val = getattr(o, "children", None)
        children_count = children_val if isinstance(children_val, int) else 0
        people_str = f"👥 {adults_count} os. dorosłe" + (f", {children_count} dzieci" if children_count > 0 else "")
        
        dep_date = getattr(o, "departure_date", None)
        dur_nights = getattr(o, "duration_nights", None)
        nights_str = f"📅 {dep_date}" if isinstance(dep_date, str) or hasattr(dep_date, "isoformat") else ""
        if isinstance(dur_nights, int):
            nights_str += f" ({dur_nights} nocy)"
        
        dep_city = getattr(o, "departure_city", None)
        dep_str = f"✈️ Wylot z: {dep_city}" if isinstance(dep_city, str) else ""
        
        meal_val = getattr(o, "meal_type", None)
        meal_str = f"🍽️ {meal_val}" if isinstance(meal_val, str) else ""
        
        ppp_val = getattr(o, "price_per_person", None)
        ppp = f"{ppp_val:.0f}" if isinstance(ppp_val, (int, float, Decimal)) else (str(ppp_val) if isinstance(ppp_val, str) else None)
        
        total_val = getattr(o, "price_total", None)
        currency_val = getattr(o, "currency", "PLN")
        currency_str = str(currency_val) if isinstance(currency_val, str) else "PLN"
        total_p = f" (Łącznie: {total_val:.0f} {currency_str})" if isinstance(total_val, (int, float, Decimal)) else ""
        
        score_val = getattr(o, "travel_score", None)
        score_str = f" | 🏆 Score: <b>{score_val}</b>/100" if isinstance(score_val, (int, float)) else ""

        lines.append("")
        if hotel_name_str:
            lines.append(f"🏨 <b>{hotel_name_str}</b>{stars_str}{rating_str}")
        if country_str:
            lines.append(f"📍 <b>{country_str}</b>{region_str}")
        
        details_row = " | ".join([s for s in [nights_str, dep_str] if s])
        if details_row:
            lines.append(details_row)
            
        meals_row = " | ".join([s for s in [meal_str, people_str] if s])
        if meals_row:
            lines.append(meals_row)
            
        if ppp:
            lines.append(f"💰 <b>{ppp} PLN/os.</b>{total_p}{score_str}")
            
        lines.append(f"🏢 <b>Biuro podróży:</b> {provider_name}")
        
        if offer_url:
            lines.append(f'🔗 <a href="{offer_url}">Otwórz ofertę w {provider_name}</a>')

    return "\n".join(lines)


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
        """Send notifications for a batch of alerts.

        Returns the number of successfully delivered notifications.
        """
        if not self._channels:
            return 0

        if not alerts:
            return 0

        delivered = 0

        for alert in alerts:
            message = format_alert_message(alert)
            for channel in self._channels:
                try:
                    success = await channel.send(alert, message)
                    if success:
                        delivered += 1
                except Exception:
                    logger.exception(
                        "Channel %s failed for alert %s",
                        type(channel).__name__,
                        alert.id,
                    )

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
