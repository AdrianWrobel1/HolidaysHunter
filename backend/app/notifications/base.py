"""Abstract notification channel interface.

Each notification channel (Telegram, e-mail, push) implements this interface.
The NotificationService dispatches to all registered channels without
knowing the delivery details.
"""

from abc import ABC, abstractmethod

from app.models.alert_event import AlertEvent


class NotificationChannel(ABC):
    """Base class for notification delivery channels."""

    @abstractmethod
    async def send(self, alert: AlertEvent, formatted_message: str) -> bool:
        """Send a single notification.

        Args:
            alert: The alert event to notify about.
            formatted_message: Pre-formatted message text.

        Returns:
            True if delivery succeeded, False otherwise.
        """

    @abstractmethod
    async def close(self) -> None:
        """Release any resources held by the channel."""
