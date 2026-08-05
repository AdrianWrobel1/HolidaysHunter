"""Tests for the notification system — Telegram channel and notification service."""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import AlertType
from app.notifications.service import (
    NotificationService,
    format_alert_message,
)
from app.notifications.telegram import TelegramChannel


def _mock_alert(**overrides):
    """Create a mock AlertEvent for testing."""
    alert = MagicMock()
    alert.id = overrides.get("id", uuid.uuid4())
    alert.offer_id = overrides.get("offer_id", uuid.uuid4())
    alert.profile_id = overrides.get("profile_id", None)
    alert.alert_type = overrides.get("alert_type", AlertType.NEW_MATCH)
    alert.message = overrides.get(
        "message", "Nowa oferta: Hotel Sun, Grecja - 2250 PLN/os."
    )
    alert.metadata_json = overrides.get("metadata_json", {
        "price_per_person": "2250.00",
    })
    alert.is_read = overrides.get("is_read", False)
    alert.triggered_at = overrides.get(
        "triggered_at", datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)
    )

    offer = MagicMock()
    offer.offer_url = overrides.get("offer_url", "https://itaka.pl/offer/123")
    alert.offer = offer

    return alert


class TestFormatAlertMessage:
    def test_new_match_format(self):
        alert = _mock_alert(alert_type=AlertType.NEW_MATCH)
        msg = format_alert_message(alert)
        assert "<b>Nowa oferta</b>" in msg
        assert alert.message in msg
        assert "Otwórz ofertę" in msg

    def test_price_drop_format(self):
        alert = _mock_alert(
            alert_type=AlertType.PRICE_DROP,
            message="Spadek ceny: Hotel Sun",
            metadata_json={
                "previous_price": "2500",
                "current_price": "2000",
                "change_pct": -20.0,
            },
        )
        msg = format_alert_message(alert)
        assert "<b>Spadek ceny</b>" in msg
        assert "2500" in msg
        assert "2000" in msg

    def test_high_score_format(self):
        alert = _mock_alert(
            alert_type=AlertType.HIGH_SCORE,
            message="Wysoki Travel Score",
            metadata_json={"travel_score": 85},
        )
        msg = format_alert_message(alert)
        assert "<b>Wysoki Travel Score</b>" in msg
        assert "85/100" in msg

    def test_lowest_price_format(self):
        alert = _mock_alert(
            alert_type=AlertType.LOWEST_PRICE,
            message="Najnizsza cena",
            metadata_json={
                "current_price": "1700",
                "previous_min": "1900",
                "lookback_days": 30,
            },
        )
        msg = format_alert_message(alert)
        assert "<b>Najnizsza cena</b>" in msg
        assert "1900" in msg

    def test_reappeared_format(self):
        alert = _mock_alert(alert_type=AlertType.REAPPEARED)
        msg = format_alert_message(alert)
        assert "<b>Oferta powrocila</b>" in msg

    def test_offer_link_included(self):
        alert = _mock_alert()
        msg = format_alert_message(alert)
        assert "https://itaka.pl/offer/123" in msg


class TestTelegramChannel:
    def test_not_configured_without_credentials(self):
        with patch("app.notifications.telegram.settings") as mock_settings:
            mock_settings.telegram_bot_token = ""
            mock_settings.telegram_chat_id = ""
            channel = TelegramChannel()
            assert channel.is_configured is False

    def test_configured_with_credentials(self):
        with patch("app.notifications.telegram.settings") as mock_settings:
            mock_settings.telegram_bot_token = "123:ABC"
            mock_settings.telegram_chat_id = "456"
            channel = TelegramChannel()
            assert channel.is_configured is True

    @pytest.mark.asyncio
    async def test_send_skips_when_not_configured(self):
        with patch("app.notifications.telegram.settings") as mock_settings:
            mock_settings.telegram_bot_token = ""
            mock_settings.telegram_chat_id = ""
            channel = TelegramChannel()
            alert = _mock_alert()
            result = await channel.send(alert, "test message")
            assert result is False
            await channel.close()

    @pytest.mark.asyncio
    async def test_send_success(self):
        with patch("app.notifications.telegram.settings") as mock_settings:
            mock_settings.telegram_bot_token = "123:ABC"
            mock_settings.telegram_chat_id = "456"
            channel = TelegramChannel()

            mock_response = MagicMock()
            mock_response.status_code = 200
            channel._client = AsyncMock()
            channel._client.post = AsyncMock(return_value=mock_response)

            alert = _mock_alert()
            result = await channel.send(alert, "test message")
            assert result is True

            channel._client.post.assert_called_once()
            call_args = channel._client.post.call_args
            assert "sendMessage" in call_args[0][0]
            assert call_args[1]["json"]["text"] == "test message"
            assert call_args[1]["json"]["parse_mode"] == "HTML"

    @pytest.mark.asyncio
    async def test_send_failure_returns_false(self):
        with patch("app.notifications.telegram.settings") as mock_settings:
            mock_settings.telegram_bot_token = "123:ABC"
            mock_settings.telegram_chat_id = "456"
            channel = TelegramChannel()

            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad Request"
            channel._client = AsyncMock()
            channel._client.post = AsyncMock(return_value=mock_response)

            alert = _mock_alert()
            result = await channel.send(alert, "test message")
            assert result is False


class TestNotificationService:
    @pytest.mark.asyncio
    async def test_dispatch_empty_alerts(self):
        with patch("app.notifications.service.TelegramChannel") as MockTelegram:
            instance = AsyncMock()
            instance.is_configured = True
            MockTelegram.return_value = instance

            service = NotificationService()
            delivered = await service.dispatch([])
            assert delivered == 0

    @pytest.mark.asyncio
    async def test_dispatch_sends_to_channels(self):
        with patch("app.notifications.service.TelegramChannel") as MockTelegram:
            instance = AsyncMock()
            instance.is_configured = True
            instance.send = AsyncMock(return_value=True)
            MockTelegram.return_value = instance

            service = NotificationService()
            alerts = [_mock_alert(), _mock_alert()]
            delivered = await service.dispatch(alerts)
            assert delivered == 2
            assert instance.send.call_count == 2

    @pytest.mark.asyncio
    async def test_dispatch_handles_channel_failure(self):
        with patch("app.notifications.service.TelegramChannel") as MockTelegram:
            instance = AsyncMock()
            instance.is_configured = True
            instance.send = AsyncMock(side_effect=Exception("Connection error"))
            MockTelegram.return_value = instance

            service = NotificationService()
            alerts = [_mock_alert()]
            delivered = await service.dispatch(alerts)
            assert delivered == 0

    @pytest.mark.asyncio
    async def test_no_channels_when_not_configured(self):
        with patch("app.notifications.service.TelegramChannel") as MockTelegram:
            instance = AsyncMock()
            instance.is_configured = False
            MockTelegram.return_value = instance

            service = NotificationService()
            assert len(service._channels) == 0
