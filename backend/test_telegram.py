"""Test script for Telegram Bot integration.

Run this script to verify that your Telegram Bot token and Chat ID are configured correctly.

Usage:
    cd backend
    .venv\\Scripts\\activate
    python test_telegram.py
"""

import asyncio
import sys

from app.core.config import settings
from app.notifications.telegram import TelegramChannel


async def test_telegram_connection() -> None:
    print("=" * 60)
    print("🧪 Test Bota Telegrama HolidaysHunter")
    print("=" * 60)

    token = settings.telegram_bot_token
    chat_id = settings.telegram_chat_id

    print(f"• TELEGRAM_BOT_TOKEN: {'✅ Ustawiony' if token else '❌ Brak (ustaw w .env)'}")
    print(f"• TELEGRAM_CHAT_ID:   {'✅ Ustawiony' if chat_id else '❌ Brak (ustaw w .env)'}")
    print("-" * 60)

    if not token or not chat_id:
        print("❌ Uzupełnij TELEGRAM_BOT_TOKEN oraz TELEGRAM_CHAT_ID w pliku backend/.env!")
        print("Instrukcja:")
        print(" 1. Napisz do @BotFather w Telegramie -> /newbot")
        print(" 2. Pobierz token i wklej do backend/.env jako TELEGRAM_BOT_TOKEN")
        print(" 3. Napisz dowolną wiadomość do bota i pobierz swój ID z @userinfobot")
        print(" 4. Wklej swój ID do backend/.env jako TELEGRAM_CHAT_ID")
        sys.exit(1)

    channel = TelegramChannel()
    message = (
        "🚀 <b>Test powiadomienia HolidaysHunter!</b>\n\n"
        "Twój Bot Telegrama został pomyślnie skonfigurowany i działa poprawnie! 🎉\n"
        "Wpisz <b>/help</b> lub <b>/status</b> na czacie, aby przetestować komendy."
    )

    print("Sending test message via Telegram API...")
    # Mock a minimal AlertEvent structure or test send
    from unittest.mock import MagicMock
    dummy_alert = MagicMock()
    dummy_alert.alert_type = "test_event"

    success = await channel.send(dummy_alert, message)
    await channel.close()

    if success:
        print("\n✅ SUKCES! Wiadomość testowa dotarła na Twój Telegram!")
    else:
        print("\n❌ BŁĄD! Nie udało się wysłać wiadomości. Sprawdź poprawność Tokenu i Chat ID.")


if __name__ == "__main__":
    asyncio.run(test_telegram_connection())
