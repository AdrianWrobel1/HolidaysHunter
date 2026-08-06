"""Telegram notification channel adapter — delivers alerts via unified Telegram bot listener."""

import logging

from app.core.config import settings
from app.models.alert_event import AlertEvent
from app.notifications.base import NotificationChannel
from app.notifications.telegram_bot import telegram_bot_listener

logger = logging.getLogger(__name__)


class TelegramChannel(NotificationChannel):
    """Channel adapter sending alert notifications via unified V3 TelegramBotListener."""

    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        telegram_bot_listener.set_enabled(enabled)

    @classmethod
    def get_enabled(cls) -> bool:
        return telegram_bot_listener.get_enabled()

    @property
    def _bot_token(self) -> str:
        return settings.telegram_bot_token

    @property
    def _chat_id(self) -> str:
        return settings.telegram_chat_id

    @property
    def _client(self):
        """Access shared HTTP client or listener client for compatibility/testing."""
        return telegram_bot_listener._client

    @_client.setter
    def _client(self, client) -> None:
        telegram_bot_listener._client = client

    @property
    def is_configured(self) -> bool:
        """Check if Telegram credentials are set and notifications are enabled."""
        return bool(self._bot_token and self._chat_id and telegram_bot_listener.get_enabled())

    async def send(
        self,
        alert: AlertEvent,
        formatted_message: str,
        reply_markup: dict | None = None,
    ) -> bool:
        """Send a message to the configured Telegram chat via V3 listener."""
        if not self.is_configured:
            logger.debug("Telegram not configured, skipping notification")
            return False
        return await telegram_bot_listener.send(alert, formatted_message, reply_markup)

    async def close(self) -> None:
        """Close resources (lifecycle managed globally by telegram_bot_listener)."""
        await telegram_bot_listener.close()
