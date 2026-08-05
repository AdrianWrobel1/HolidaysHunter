"""Interactive Telegram Bot Listener.

Handles user commands on Telegram (/start, /status, /promocje, /profile, /szukaj)
via long-polling and responds using database queries.
"""

import asyncio
import logging
from typing import Any

import httpx
from sqlalchemy import func, select

from app.core.config import settings
from app.database.session import async_session_factory
from app.models.offer import Offer
from app.models.travel_profile import TravelProfile

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


class TelegramBotListener:
    """Long-polling background worker that listens for Telegram messages and handles commands."""

    def __init__(self) -> None:
        self._bot_token = settings.telegram_bot_token
        self._allowed_chat_id = settings.telegram_chat_id
        self._client: httpx.AsyncClient | None = None
        self._offset = 0
        self._is_running = False
        self._task: asyncio.Task[None] | None = None

    @property
    def is_configured(self) -> bool:
        """Check if Telegram token is present."""
        return bool(self._bot_token)

    async def start(self) -> None:
        """Start long-polling in background task."""
        if not self.is_configured:
            logger.info("Telegram Bot Listener: bot token not set, listener disabled")
            return

        self._client = httpx.AsyncClient(timeout=30.0)
        self._is_running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Telegram Bot Listener started")

    async def stop(self) -> None:
        """Stop background long-polling task."""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._client:
            await self._client.aclose()
        logger.info("Telegram Bot Listener stopped")

    async def _poll_loop(self) -> None:
        """Main long-polling loop."""
        url = f"{TELEGRAM_API_BASE}/bot{self._bot_token}/getUpdates"

        while self._is_running:
            try:
                response = await self._client.get(
                    url,
                    params={"offset": self._offset, "timeout": 20},
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get("ok"):
                        updates = data.get("result", [])
                        for update in updates:
                            self._offset = update["update_id"] + 1
                            await self._handle_update(update)
                else:
                    logger.warning("Telegram getUpdates returned %d", response.status_code)
                    await asyncio.sleep(5)
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Error in Telegram Bot poll loop")
                await asyncio.sleep(5)

    async def _send_reply(self, chat_id: int | str, text: str) -> None:
        """Send HTML formatted reply to user."""
        if not self._client or not self._bot_token:
            return

        url = f"{TELEGRAM_API_BASE}/bot{self._bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        try:
            await self._client.post(url, json=payload)
        except Exception:
            logger.exception("Failed to send reply to chat %s", chat_id)

    async def _handle_update(self, update: dict[str, Any]) -> None:
        """Process incoming telegram update."""
        message = update.get("message")
        if not message or "text" not in message:
            return

        chat_id = message["chat"]["id"]
        # Security check: if telegram_chat_id is specified in settings, ignore messages from other users
        if self._allowed_chat_id and str(chat_id) != str(self._allowed_chat_id):
            logger.warning("Received message from unauthorized chat_id: %s", chat_id)
            return

        text = message["text"].strip()
        cmd = text.split()[0].lower() if text else ""
        args = text.split()[1:] if len(text.split()) > 1 else []

        if cmd in ("/start", "/help"):
            await self._cmd_help(chat_id)
        elif cmd == "/status":
            await self._cmd_status(chat_id)
        elif cmd in ("/promocje", "/top"):
            await self._cmd_promocje(chat_id)
        elif cmd == "/profile":
            await self._cmd_profile(chat_id)
        elif cmd == "/szukaj":
            await self._cmd_szukaj(chat_id, " ".join(args))
        elif cmd == "/skanuj":
            await self._cmd_skanuj(chat_id)
        else:
            await self._send_reply(
                chat_id,
                "❓ Nie rozumiem tej komendy. Wpisz /help, aby zobaczyć dostępne komendy.",
            )

    async def _cmd_help(self, chat_id: int | str) -> None:
        lines = [
            "🤖 <b>Witaj w Bocie HolidaysHunter!</b>",
            "",
            "Oto dostępne komendy:",
            "• /status — Sprawdź stan bazy ofert, skanera i profili",
            "• /promocje — Zobacz TOP 5 najlepszych okazji (Travel Score)",
            "• /skanuj — Uruchom natychmiastowe pobieranie świeżych okazji ze wszystkich biur!",
            "• /profile — Wyświetl Twoje zapisane profile podróży (ze strony)",
            "• /szukaj [kraj/region] — Wyszukaj oferty (np. <code>/szukaj Turcja</code>)",
            "• /help — Wyświetl tę pomoc",
        ]
        await self._send_reply(chat_id, "\n".join(lines))

    async def _cmd_status(self, chat_id: int | str) -> None:
        async with async_session_factory() as session:
            count_offers = (
                await session.execute(
                    select(func.count(Offer.id)).where(Offer.is_available.is_(True))
                )
            ).scalar() or 0

            count_profiles = (
                await session.execute(
                    select(func.count(TravelProfile.id)).where(
                        TravelProfile.is_active.is_(True)
                    )
                )
            ).scalar() or 0

            last_offer = (
                await session.execute(
                    select(Offer).order_by(Offer.last_seen_at.desc()).limit(1)
                )
            ).scalar_one_or_none()

            last_update_str = (
                last_offer.last_seen_at.strftime("%Y-%m-%d %H:%M")
                if last_offer and last_offer.last_seen_at
                else "Brak danych"
            )

        lines = [
            "📊 <b>Statystyki HolidaysHunter</b>",
            "",
            f"• <b>Dostępne oferty w bazie:</b> {count_offers}",
            f"• <b>Aktywne profile podróży:</b> {count_profiles}",
            f"• <b>Ostatnia aktualizacja ofert:</b> {last_update_str}",
            f"• <b>Harmonogram skanowania:</b> Co {settings.import_interval_minutes} minut (automatycznie 24/7)",
            "• <b>Status serwera:</b> 🟢 Działa",
        ]
        await self._send_reply(chat_id, "\n".join(lines))

    async def _cmd_skanuj(self, chat_id: int | str) -> None:
        await self._send_reply(
            chat_id,
            "🔄 <b>Uruchamiam skanowanie okazji z biur podróży...</b>\n"
            "Pobieram najświeższe dane z Itaka, TUI, Rainbow i Wakacje.pl. "
            "Jeśli znajdę nowe super okazje pasujące do Twoich alertów, otrzymasz od razu powiadomienie!"
        )
        
        from app.models.enums import Provider
        from app.services.import_service import run_import
        
        success_providers = []
        async with async_session_factory() as session:
            for p in Provider:
                try:
                    await run_import(p, session)
                    success_providers.append(p.value.upper())
                except Exception as e:
                    logger.exception("Manual Telegram scan failed for %s", p.value)
            await session.commit()
            
        await self._send_reply(
            chat_id,
            f"✅ <b>Skanowanie zakończone!</b>\n"
            f"Zaktualizowano oferty z biur: {', '.join(success_providers)}.\n"
            f"Wpisz /promocje aby zobaczyć aktualne TOP okazje!"
        )

    async def _cmd_promocje(self, chat_id: int | str) -> None:
        async with async_session_factory() as session:
            offers = (
                (
                    await session.execute(
                        select(Offer)
                        .where(Offer.is_available.is_(True))
                        .order_by(Offer.travel_score.desc().nullslast(), Offer.price_per_person.asc())
                        .limit(5)
                    )
                )
                .scalars()
                .all()
            )

        from app.providers.schemas import build_direct_offer_url

        if not offers:
            await self._send_reply(chat_id, "ℹ️ Brak dostępnych ofert w bazie danych.")
            return

        lines = ["🔥 <b>TOP 5 Okazji Wakacyjnych (Travel Score)</b>\n"]
        for idx, o in enumerate(offers, 1):
            stars = f" {'⭐' * int(o.hotel_stars)}" if o.hotel_stars else ""
            score = f" | 🏆 Score: <b>{o.travel_score}</b>/100" if o.travel_score else ""
            region_str = f" • {o.region}" if o.region else ""
            
            adults_cnt = o.adults or 2
            children_cnt = o.children or 0
            people_str = f"👥 {adults_cnt} os." + (f", {children_cnt} dzieci" if children_cnt > 0 else "")
            total_str = f" (Łącznie: {o.price_total:.0f} PLN)" if o.price_total else ""

            clean_url = build_direct_offer_url(o.provider, str(o.external_id or o.id), o.offer_url) or o.offer_url

            lines.append(
                f"{idx}. 🏨 <b>{o.hotel_name}</b>{stars}\n"
                f"   📍 {o.country}{region_str}\n"
                f"   📅 {o.departure_date} ({o.duration_nights} nocy) | ✈️ {o.departure_city}\n"
                f"   🍽️ {o.meal_type} | {people_str}\n"
                f"   💰 <b>{o.price_per_person:.0f} PLN/os.</b>{total_str}{score}\n"
                f"   🔗 <a href=\"{clean_url}\">Otwórz ofertę w {o.provider.upper()}</a>\n"
            )

        await self._send_reply(chat_id, "\n".join(lines))

    async def _cmd_profile(self, chat_id: int | str) -> None:
        async with async_session_factory() as session:
            profiles = (
                (
                    await session.execute(
                        select(TravelProfile).order_by(TravelProfile.id.asc())
                    )
                )
                .scalars()
                .all()
            )

        if not profiles:
            await self._send_reply(
                chat_id, "ℹ️ Nie masz jeszcze zapisanych żadnych profili podróży na stronie."
            )
            return

        lines = ["⚙️ <b>Twoje zapisane profile podróży (ze strony)</b>\n"]
        for p in profiles:
            status = "🟢 Aktywny" if p.is_active else "🔴 Nieaktywny"
            countries = ", ".join(p.countries) if p.countries else "Wszystkie kraje"
            budget = f"do {p.budget_max:.0f} PLN/os." if p.budget_max else "Bez limitu"
            dep = ", ".join(p.departure_cities) if p.departure_cities else "Wszystkie lotniska"
            dur = f"{p.duration_min or 1}-{p.duration_max or 14} nocy"
            ppl = f"{p.adults or 2} dorusłych" + (f", {p.children} dzieci" if p.children else "")

            lines.append(
                f"• <b>{p.name}</b> [{status}]\n"
                f"   🌍 Kraje: {countries}\n"
                f"   ✈️ Wylot z: {dep}\n"
                f"   🌙 Pobyt: {dur} | 👥 Osoby: {ppl}\n"
                f"   💵 Max budżet: {budget}\n"
            )

        await self._send_reply(chat_id, "\n".join(lines))

    async def _cmd_szukaj(self, chat_id: int | str, query: str) -> None:
        if not query:
            await self._send_reply(
                chat_id, "❓ Podaj kraj lub region po komendzie, np.:\n<code>/szukaj Turcja</code>"
            )
            return

        async with async_session_factory() as session:
            pattern = f"%{query}%"
            offers = (
                (
                    await session.execute(
                        select(Offer)
                        .where(
                            Offer.is_available.is_(True),
                            (
                                Offer.country.ilike(pattern)
                                | Offer.region.ilike(pattern)
                                | Offer.title.ilike(pattern)
                                | Offer.hotel_name.ilike(pattern)
                            ),
                        )
                        .order_by(Offer.travel_score.desc().nullslast(), Offer.price_per_person.asc())
                        .limit(5)
                    )
                )
                .scalars()
                .all()
            )

        if not offers:
            await self._send_reply(
                chat_id, f"ℹ️ Nie znaleziono ofert pasujących do frazy: <b>{query}</b>"
            )
            return

        from app.providers.schemas import build_direct_offer_url

        lines = [f"🔍 <b>Wyniki wyszukiwania dla: {query}</b>\n"]
        for idx, o in enumerate(offers, 1):
            stars = f" {'⭐' * int(o.hotel_stars)}" if o.hotel_stars else ""
            score = f" | 🏆 Score: <b>{o.travel_score}</b>/100" if o.travel_score else ""
            region_str = f" • {o.region}" if o.region else ""

            adults_cnt = o.adults or 2
            children_cnt = o.children or 0
            people_str = f"👥 {adults_cnt} os." + (f", {children_cnt} dzieci" if children_cnt > 0 else "")
            total_str = f" (Łącznie: {o.price_total:.0f} PLN)" if o.price_total else ""

            clean_url = build_direct_offer_url(o.provider, str(o.external_id or o.id), o.offer_url) or o.offer_url

            lines.append(
                f"{idx}. 🏨 <b>{o.hotel_name}</b>{stars}\n"
                f"   📍 {o.country}{region_str}\n"
                f"   📅 {o.departure_date} ({o.duration_nights} nocy) | ✈️ {o.departure_city}\n"
                f"   🍽️ {o.meal_type} | {people_str}\n"
                f"   💰 <b>{o.price_per_person:.0f} PLN/os.</b>{total_str}{score}\n"
                f"   🔗 <a href=\"{clean_url}\">Otwórz ofertę w {o.provider.upper()}</a>\n"
            )

        await self._send_reply(chat_id, "\n".join(lines))


# Singleton instance
telegram_bot_listener = TelegramBotListener()
