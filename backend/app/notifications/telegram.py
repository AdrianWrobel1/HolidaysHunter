"""Telegram notification channel — delivers alerts via Telegram Bot API."""

import logging

import httpx

from app.core.config import settings
from app.models.alert_event import AlertEvent
from app.notifications.base import NotificationChannel

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramChannel(NotificationChannel):
    """Sends alert messages to a Telegram chat via Bot API."""

    _enabled: bool = True

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(timeout=10.0)
        self._bot_token = settings.telegram_bot_token
        self._chat_id = settings.telegram_chat_id

    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        cls._enabled = enabled

    @classmethod
    def get_enabled(cls) -> bool:
        return cls._enabled

    @property
    def is_configured(self) -> bool:
        """Check if Telegram credentials are set and notifications are enabled."""
        return bool(self._bot_token and self._chat_id and self._enabled)

    async def send(self, alert: AlertEvent, formatted_message: str) -> bool:
        """Send a message to the configured Telegram chat."""
        if not self.is_configured:
            logger.debug("Telegram not configured, skipping notification")
            return False

        url = f"{TELEGRAM_API_BASE}/bot{self._bot_token}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": formatted_message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }

        try:
            response = await self._client.post(url, json=payload)
            if response.status_code == 200:
                logger.info("Telegram notification sent: %s", alert.alert_type)
                return True
            logger.warning(
                "Telegram API returned %d: %s",
                response.status_code,
                response.text[:200],
            )
            return False
        except httpx.HTTPError:
            logger.exception("Failed to send Telegram notification")
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()
