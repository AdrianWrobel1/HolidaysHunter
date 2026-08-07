"""Interactive Telegram Bot Listener.

Handles user commands (/start, /status, /promocje, /profiles, /szukaj, /skanuj,
/delete_profile, /pause_profile, /resume_profile, /profile_info, /edit_profile)
and Telegram Inline Keyboard Callback Queries via long-polling.
"""

import asyncio
from datetime import datetime, timezone
import logging
import os
import sys
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.database.session import async_session_factory
from app.models.offer import Offer
from app.models.travel_profile import TravelProfile
from app.models.watchlist import OfferIgnore, OfferWatchlist
from app.services.watchlist_service import add_to_watchlist, ignore_offer

logger = logging.getLogger(__name__)

TELEGRAM_API_BASE = "https://api.telegram.org"


class ProcessLock:
    """Cross-platform non-blocking file lock to prevent multiple poller instances."""

    def __init__(self, lock_file_path: str):
        self.lock_file_path = lock_file_path
        self._file_handle: Any = None

    def acquire(self) -> bool:
        try:
            if sys.platform == "win32":
                import msvcrt
                self._file_handle = os.open(self.lock_file_path, os.O_CREAT | os.O_RDWR)
                msvcrt.locking(self._file_handle, msvcrt.LK_NBLCK, 1)
                os.ftruncate(self._file_handle, 0)
                os.write(self._file_handle, str(os.getpid()).encode("utf-8"))
                return True
            else:
                import fcntl
                self._file_handle = open(self.lock_file_path, "w")
                fcntl.flock(self._file_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._file_handle.write(str(os.getpid()))
                self._file_handle.flush()
                return True
        except (IOError, OSError):
            if self._file_handle is not None:
                try:
                    if isinstance(self._file_handle, int):
                        os.close(self._file_handle)
                    else:
                        self._file_handle.close()
                except Exception:
                    pass
                self._file_handle = None
            return False

    def release(self) -> None:
        if self._file_handle is not None:
            try:
                if sys.platform == "win32":
                    import msvcrt
                    os.lseek(self._file_handle, 0, os.SEEK_SET)
                    msvcrt.locking(self._file_handle, msvcrt.LK_UNLCK, 1)
                    os.close(self._file_handle)
                else:
                    import fcntl
                    fcntl.flock(self._file_handle.fileno(), fcntl.LOCK_UN)
                    self._file_handle.close()
            except Exception:
                pass
            self._file_handle = None
            try:
                if os.path.exists(self.lock_file_path):
                    os.remove(self.lock_file_path)
            except Exception:
                pass


PROCESS_START_TIME = datetime.now(timezone.utc).isoformat()

# Transport Icons & Labels mapping for Telegram replies
_TRANSPORT_ICONS: dict[str, str] = {
    "flight": "✈️ Przelot samolotem",
    "self_transport": "🚗 Dojazd własny",
    "own": "🚗 Dojazd własny",
    "bus": "🚌 Autokar",
    "train": "🚆 Pociąg",
    "cruise": "🚢 Rejs",
    "unknown": "❓ Nieokreślony transport",
}

_POLICY_NEXT: dict[str, str] = {
    "HIGH_AND_MUST_SEE": "MUST_SEE_ONLY",
    "MUST_SEE_ONLY": "ALL_ALERTS",
    "ALL_ALERTS": "DAILY_DIGEST",
    "DAILY_DIGEST": "HIGH_AND_MUST_SEE",
}

_POLICY_LABELS: dict[str, str] = {
    "HIGH_AND_MUST_SEE": "MUST SEE + HIGH 🔥",
    "MUST_SEE_ONLY": "Tylko MUST SEE 🔥🔥🔥",
    "ALL_ALERTS": "Wszystkie alerty 📌",
    "DAILY_DIGEST": "Zbiorczo dziennie 📰",
}


class TelegramBotListener:
    """Long-polling background worker that listens for Telegram messages & callback queries."""

    _enabled: bool = True

    def __init__(self) -> None:
        self._bot_token = settings.telegram_bot_token
        self._allowed_chat_id = settings.telegram_chat_id
        self._client: httpx.AsyncClient | None = None
        self._offset = 0
        self._is_running = False
        self._task: asyncio.Task[None] | None = None
        self._lock = ProcessLock(os.path.abspath("telegram_bot.lock"))
        self._bot_username: str = ""
        self._bot_id: int | None = None

    @classmethod
    def set_enabled(cls, enabled: bool) -> None:
        cls._enabled = enabled

    @classmethod
    def get_enabled(cls) -> bool:
        return cls._enabled

    @property
    def is_configured(self) -> bool:
        """Check if Telegram token is present and enabled."""
        return bool(self._bot_token and self._enabled)

    async def start(self) -> None:
        """Start long-polling in background task with startup protection and diagnostics."""
        if not self.is_configured:
            logger.info("Telegram Bot Listener: bot token not set, listener disabled")
            return

        if self._is_running:
            logger.warning("Telegram Bot Listener is already running in this process")
            return

        if not self._lock.acquire():
            logger.error(
                "[ERROR] Another TelegramBotListener process is already running. "
                "Aborting startup to enforce a single Telegram polling loop."
            )
            return

        self._client = httpx.AsyncClient(timeout=30.0)

        # Telegram getMe verification
        try:
            get_me_res = await self._client.get(f"{TELEGRAM_API_BASE}/bot{self._bot_token}/getMe")
            if get_me_res.status_code != 200:
                logger.error("Telegram getMe verification failed: status %d", get_me_res.status_code)
                self._lock.release()
                await self._client.aclose()
                return
            data = get_me_res.json()
            if not data.get("ok"):
                logger.error("Telegram getMe verification failed: %s", data)
                self._lock.release()
                await self._client.aclose()
                return

            result = data.get("result", {})
            self._bot_username = result.get("username", "Unknown")
            self._bot_id = result.get("id")
        except Exception:
            logger.exception("Failed getMe verification on Telegram API")
            self._lock.release()
            await self._client.aclose()
            return

        # Ensure no leftover webhook exists
        try:
            await self._client.post(f"{TELEGRAM_API_BASE}/bot{self._bot_token}/deleteWebhook")
        except Exception:
            logger.warning("Could not delete Telegram webhook during startup")

        fp = f"{self._bot_token[:4]}...{self._bot_token[-4:]}" if len(self._bot_token) > 8 else "***"
        env_path = os.path.abspath(".env") if os.path.exists(".env") else "Environment variables"

        logger.info(
            "[TELEGRAM BOT STARTUP DIAGNOSTICS]\n"
            "  PID:               %d\n"
            "  Process Start:     %s\n"
            "  Bot Username:      @%s\n"
            "  Bot ID:            %s\n"
            "  Token Fingerprint: %s\n"
            "  Working Dir:       %s\n"
            "  Loaded .env:       %s\n"
            "  Status:            Polling started",
            os.getpid(),
            PROCESS_START_TIME,
            self._bot_username,
            self._bot_id,
            fp,
            os.getcwd(),
            env_path,
        )

        self._is_running = True
        self._task = asyncio.create_task(self._poll_loop())

    async def stop(self) -> None:
        """Stop background long-polling task and release lock."""
        self._is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._client:
            await self._client.aclose()
        self._lock.release()
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

    async def send_message(
        self,
        chat_id: int | str,
        text: str,
        reply_markup: dict[str, Any] | None = None,
        disable_web_page_preview: bool = True,
    ) -> bool:
        """Send HTML formatted message to user, optionally with inline reply_markup buttons."""
        bot_token = self._bot_token or settings.telegram_bot_token
        target_chat = chat_id or self._allowed_chat_id or settings.telegram_chat_id
        if not bot_token or not target_chat:
            logger.debug("Telegram send_message: bot_token or chat_id not configured")
            return False

        client_created = False
        client = self._client
        if client is None:
            client = httpx.AsyncClient(timeout=10.0)
            client_created = True

        url = f"{TELEGRAM_API_BASE}/bot{bot_token}/sendMessage"
        payload: dict[str, Any] = {
            "chat_id": str(target_chat),
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": disable_web_page_preview,
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                logger.info("Telegram message sent successfully to chat %s", target_chat)
                return True
            logger.warning(
                "Telegram sendMessage returned status %d: %s",
                response.status_code,
                response.text[:200],
            )
            return False
        except Exception:
            logger.exception("Failed to send Telegram message to chat %s", target_chat)
            return False
        finally:
            if client_created:
                await client.aclose()

    async def send(
        self,
        alert: Any,
        formatted_message: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> bool:
        """Send an alert message via V3 Telegram channel."""
        if not self.is_configured:
            logger.debug("Telegram not configured, skipping notification")
            return False

        target_chat = settings.telegram_chat_id or self._allowed_chat_id
        return await self.send_message(
            chat_id=target_chat,
            text=formatted_message,
            reply_markup=reply_markup,
            disable_web_page_preview=False,
        )

    async def close(self) -> None:
        """Close client if not managed by long-polling background task."""
        if not self._is_running and self._client:
            await self._client.aclose()
            self._client = None

    async def _send_reply(
        self,
        chat_id: int | str,
        text: str,
        reply_markup: dict[str, Any] | None = None,
    ) -> None:
        """Send HTML formatted reply to user, optionally with inline reply_markup buttons."""
        await self.send_message(chat_id, text, reply_markup=reply_markup, disable_web_page_preview=True)

    async def _answer_callback_query(
        self,
        callback_query_id: str,
        text: str,
        show_alert: bool = False,
    ) -> None:
        """Acknowledge Telegram Callback Query button tap."""
        if not self._client or not self._bot_token:
            return

        url = f"{TELEGRAM_API_BASE}/bot{self._bot_token}/answerCallbackQuery"
        payload = {
            "callback_query_id": callback_query_id,
            "text": text,
            "show_alert": show_alert,
        }
        try:
            await self._client.post(url, json=payload)
        except Exception:
            logger.exception("Failed to answer callback query %s", callback_query_id)

    async def _handle_update(self, update: dict[str, Any]) -> None:
        """Process incoming telegram update (messages or callback queries)."""
        # Handle Callback Queries (Inline Button Taps)
        if "callback_query" in update:
            cb = update["callback_query"]
            chat_id = cb.get("message", {}).get("chat", {}).get("id")
            if self._allowed_chat_id and str(chat_id) != str(self._allowed_chat_id):
                await self._answer_callback_query(cb["id"], "Brak uprawnień.")
                return
            await self._handle_callback_query(cb)
            return

        # Handle Standard Messages
        message = update.get("message")
        if not message or "text" not in message:
            return

        chat_id = message["chat"]["id"]
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
        elif cmd in ("/profile", "/profiles"):
            await self._cmd_profiles(chat_id)
        elif cmd == "/delete_profile":
            await self._cmd_delete_profile(chat_id, args)
        elif cmd == "/pause_profile":
            await self._cmd_pause_profile(chat_id, args)
        elif cmd == "/resume_profile":
            await self._cmd_resume_profile(chat_id, args)
        elif cmd == "/profile_info":
            await self._cmd_profile_info(chat_id, args)
        elif cmd == "/edit_profile":
            await self._cmd_edit_profile(chat_id, args)
        elif cmd == "/szukaj":
            await self._cmd_szukaj(chat_id, " ".join(args))
        elif cmd == "/skanuj":
            await self._cmd_skanuj(chat_id)
        else:
            await self._send_reply(
                chat_id,
                "❓ Nie rozumiem tej komendy. Wpisz /help, aby zobaczyć dostępne komendy.",
            )

    async def _handle_callback_query(self, cb: dict[str, Any]) -> None:
        """Handle inline button click events."""
        cb_id = cb["id"]
        data = cb.get("data", "")
        chat_id = cb.get("message", {}).get("chat", {}).get("id")

        if not data or not chat_id:
            await self._answer_callback_query(cb_id, "Błąd przycisku.")
            return

        parts = data.split(":", 1)
        action = parts[0]
        payload = parts[1] if len(parts) > 1 else ""

        async with async_session_factory() as session:
            if action == "watch":
                try:
                    offer_uuid = UUID(payload)
                    await add_to_watchlist(session, str(chat_id), offer_uuid)
                    await session.commit()
                    await self._answer_callback_query(cb_id, "👀 Oferta została dodana do Obserwowanych!", show_alert=True)
                except Exception:
                    logger.exception("Failed to watch offer from callback")
                    await self._answer_callback_query(cb_id, "Nie udało się zaobserwować oferty.")

            elif action == "ignore":
                try:
                    offer_uuid = UUID(payload)
                    await ignore_offer(session, str(chat_id), offer_uuid)
                    await session.commit()
                    await self._answer_callback_query(cb_id, "🙈 Oferta trafiła na listę Ignorowanych.", show_alert=True)
                except Exception:
                    logger.exception("Failed to ignore offer from callback")
                    await self._answer_callback_query(cb_id, "Nie udało się zignorować oferty.")

            elif action in ("pause", "resume", "policy", "delete"):
                try:
                    profile_uuid = UUID(payload)
                    res = await session.execute(
                        select(TravelProfile).where(TravelProfile.id == profile_uuid)
                    )
                    profile = res.scalar_one_or_none()

                    if not profile:
                        await self._answer_callback_query(cb_id, "Profil nie istnieje.")
                        return

                    if action == "pause":
                        profile.is_active = False
                        await session.commit()
                        await self._answer_callback_query(cb_id, f"⏸ Wstrzymano profil: {profile.name}")
                    elif action == "resume":
                        profile.is_active = True
                        await session.commit()
                        await self._answer_callback_query(cb_id, f"▶ Wznowiono profil: {profile.name}")
                    elif action == "policy":
                        current_pol = profile.notification_policy or "HIGH_AND_MUST_SEE"
                        next_pol = _POLICY_NEXT.get(current_pol, "HIGH_AND_MUST_SEE")
                        profile.notification_policy = next_pol
                        await session.commit()
                        pol_lbl = _POLICY_LABELS.get(next_pol, next_pol)
                        await self._answer_callback_query(cb_id, f"🔔 Nowa polityka: {pol_lbl}", show_alert=True)
                    elif action == "delete":
                        await session.delete(profile)
                        await session.commit()
                        await self._answer_callback_query(cb_id, f"🗑 Usunięto profil: {profile.name}", show_alert=True)

                    # Refresh profiles list UI
                    await self._cmd_profiles(chat_id)
                except Exception:
                    logger.exception("Failed to process profile callback action %s", action)
                    await self._answer_callback_query(cb_id, "Błąd wykonywania akcji na profilu.")

            elif action == "profiles" and payload == "list":
                await self._answer_callback_query(cb_id, "Odświeżam listę profili...")
                await self._cmd_profiles(chat_id)

    async def _cmd_help(self, chat_id: int | str) -> None:
        lines = [
            "🤖 <b>Witaj w Bocie HolidaysHunter V3!</b>",
            "",
            "<b>Dostępne komendy:</b>",
            "• /status — Stan bazy, powiadomień i profili",
            "• /promocje — TOP okazje (Travel Score)",
            "• /skanuj — Natychmiastowe pobieranie świeżych okazji ze wszystkich biur!",
            "• /profiles — Interaktywne zarządzanie profilami z przyciskami Inline",
            "• /pause_profile [id/nr] — Wstrzymaj wysyłanie alertów dla profilu",
            "• /resume_profile [id/nr] — Wznów wysyłanie alertów dla profilu",
            "• /delete_profile [id/nr] — Usuń profil",
            "• /profile_info [id/nr] — Szczegóły kryteriów profilu",
            "• /edit_profile [id/nr] [pole=wartość] — Edytuj profil (np. <code>/edit_profile 1 budget_max=3500</code>)",
            "• /szukaj [kraj/region] — Wyszukaj oferty w bazie",
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

            count_watched = (
                await session.execute(
                    select(func.count(OfferWatchlist.id)).where(
                        OfferWatchlist.user_chat_id == str(chat_id)
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
            "📊 <b>Statystyki HolidaysHunter V3</b>",
            "",
            f"• <b>Dostępne oferty w bazie:</b> {count_offers}",
            f"• <b>Aktywne profile alertowe:</b> {count_profiles}",
            f"• <b>Obserwowane oferty:</b> {count_watched}",
            f"• <b>Ostatnie pobieranie danych:</b> {last_update_str}",
            f"• <b>Automatyczne skanowanie:</b> Co {settings.import_interval_minutes} minut 24/7",
            "• <b>Status serwera:</b> 🟢 Działa produkcyjnie",
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

            transport_badge = _TRANSPORT_ICONS.get(str(o.transport_type or "flight").lower(), "✈️ Przelot")
            clean_url = build_direct_offer_url(o.provider, str(o.external_id or o.id), o.offer_url) or o.offer_url

            lines.append(
                f"{idx}. 🏨 <b>{o.hotel_name}</b>{stars}\n"
                f"   📍 {o.country}{region_str}\n"
                f"   📅 {o.departure_date} ({o.duration_nights} nocy) | {transport_badge} (Wylot: {o.departure_city})\n"
                f"   🍽️ {o.meal_type} | {people_str}\n"
                f"   💰 <b>{o.price_per_person:.0f} PLN/os.</b>{total_str}{score}\n"
                f"   🔗 <a href=\"{clean_url}\">Otwórz ofertę w {o.provider.upper()}</a>\n"
            )

        await self._send_reply(chat_id, "\n".join(lines))

    async def _cmd_profiles(self, chat_id: int | str) -> None:
        """Display profiles with Telegram Inline Keyboard buttons for full interactive management."""
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
                chat_id,
                "ℹ️ Nie masz jeszcze utworzonych żadnych profili alertowych.\n"
                "Stwórz profil w panelu www, a pojawi się tutaj automatycznie!",
            )
            return

        lines = ["⚙️ <b>Zarządzanie Profilami Alertowymi</b>\n"]
        inline_buttons: list[list[dict[str, str]]] = []

        for idx, p in enumerate(profiles, 1):
            status_icon = "🟢 Aktywny" if p.is_active else "🔴 Nieaktywny"
            policy_lbl = _POLICY_LABELS.get(p.notification_policy, p.notification_policy or "HIGH_AND_MUST_SEE")
            countries = ", ".join(p.countries) if p.countries else "Wszystkie kraje"
            budget = f"do {p.budget_max:.0f} PLN/os." if p.budget_max else "Bez limitu"
            dep = ", ".join(p.departure_cities) if p.departure_cities else "Wszystkie wyloty"
            dur = f"{p.duration_min or 1}-{p.duration_max or 14} nocy"
            p_id = str(p.id)

            lines.append(
                f"<b>{idx}. 📂 {p.name}</b>\n"
                f"   • Status: {status_icon} | 🔔 Powiadomienia: <b>{policy_lbl}</b>\n"
                f"   • Kierunki: {countries} | Wylot: {dep}\n"
                f"   • Budżet: {budget} | Długość: {dur}\n"
            )

            # Interactive Inline Keyboard row for each profile
            toggle_action = "pause" if p.is_active else "resume"
            toggle_text = "⏸ Wstrzymaj" if p.is_active else "▶ Wznów"

            inline_buttons.append([
                {"text": f"{idx}. {toggle_text}", "callback_data": f"{toggle_action}:{p_id}"},
                {"text": "🔔 Polityka", "callback_data": f"policy:{p_id}"},
                {"text": "🗑 Usuń", "callback_data": f"delete:{p_id}"},
            ])

        keyboard = {"inline_keyboard": inline_buttons}
        await self._send_reply(chat_id, "\n".join(lines), reply_markup=keyboard)

    async def _resolve_profile_by_index_or_id(
        self, session: AsyncSession, param: str
    ) -> TravelProfile | None:
        """Resolve a profile using either a 1-based index or UUID string."""
        if not param:
            return None

        param_clean = param.strip()
        if param_clean.isdigit():
            idx = int(param_clean)
            profiles = (
                (
                    await session.execute(
                        select(TravelProfile).order_by(TravelProfile.id.asc())
                    )
                )
                .scalars()
                .all()
            )
            if 1 <= idx <= len(profiles):
                return profiles[idx - 1]
            return None

        try:
            p_uuid = UUID(param_clean)
            res = await session.execute(
                select(TravelProfile).where(TravelProfile.id == p_uuid)
            )
            return res.scalar_one_or_none()
        except ValueError:
            # Fallback to name search
            res = await session.execute(
                select(TravelProfile).where(TravelProfile.name.ilike(f"%{param_clean}%"))
            )
            return res.scalars().first()

    async def _cmd_delete_profile(self, chat_id: int | str, args: list[str]) -> None:
        """Interactive/direct profile deletion command."""
        if not args:
            await self._send_reply(
                chat_id,
                "❓ Podaj numer profilu lub ID do usunięcia, np.:\n<code>/delete_profile 1</code>\n"
                "Wpisz /profiles aby zobaczyć listę z przyciskami interaktywnymi!",
            )
            return

        async with async_session_factory() as session:
            profile = await self._resolve_profile_by_index_or_id(session, args[0])
            if not profile:
                await self._send_reply(chat_id, f"❌ Nie znaleziono profilu pasującego do: <b>{args[0]}</b>")
                return

            p_name = profile.name
            await session.delete(profile)
            await session.commit()

        await self._send_reply(chat_id, f"✅ Usunięto profil: <b>{p_name}</b>. Nie będzie już generował powiadomień!")

    async def _cmd_pause_profile(self, chat_id: int | str, args: list[str]) -> None:
        """Pause monitoring for a profile."""
        if not args:
            await self._send_reply(chat_id, "❓ Podaj numer profilu, np.: <code>/pause_profile 1</code>")
            return

        async with async_session_factory() as session:
            profile = await self._resolve_profile_by_index_or_id(session, args[0])
            if not profile:
                await self._send_reply(chat_id, f"❌ Nie znaleziono profilu pasującego do: <b>{args[0]}</b>")
                return

            profile.is_active = False
            await session.commit()
            p_name = profile.name

        await self._send_reply(chat_id, f"⏸ Wstrzymano monitoring profilu: <b>{p_name}</b>")

    async def _cmd_resume_profile(self, chat_id: int | str, args: list[str]) -> None:
        """Resume monitoring for a profile."""
        if not args:
            await self._send_reply(chat_id, "❓ Podaj numer profilu, np.: <code>/resume_profile 1</code>")
            return

        async with async_session_factory() as session:
            profile = await self._resolve_profile_by_index_or_id(session, args[0])
            if not profile:
                await self._send_reply(chat_id, f"❌ Nie znaleziono profilu pasującego do: <b>{args[0]}</b>")
                return

            profile.is_active = True
            await session.commit()
            p_name = profile.name

        await self._send_reply(chat_id, f"▶ Wznowiono monitoring profilu: <b>{p_name}</b>")

    async def _cmd_profile_info(self, chat_id: int | str, args: list[str]) -> None:
        """Display detailed criteria of a travel profile."""
        if not args:
            await self._send_reply(chat_id, "❓ Podaj numer profilu, np.: <code>/profile_info 1</code>")
            return

        async with async_session_factory() as session:
            p = await self._resolve_profile_by_index_or_id(session, args[0])
            if not p:
                await self._send_reply(chat_id, f"❌ Nie znaleziono profilu pasującego do: <b>{args[0]}</b>")
                return

            pol_lbl = _POLICY_LABELS.get(p.notification_policy, p.notification_policy or "HIGH_AND_MUST_SEE")
            lines = [
                f"📂 <b>Szczegóły profilu: {p.name}</b>",
                f"• Status: {'🟢 Aktywny' if p.is_active else '🔴 Nieaktywny'}",
                f"• Polityka alertów: <b>{pol_lbl}</b>",
                f"• Kraje: {', '.join(p.countries) if p.countries else 'Wszystkie'}",
                f"• Regiony: {', '.join(p.regions) if p.regions else 'Wszystkie'}",
                f"• Wylot z: {', '.join(p.departure_cities) if p.departure_cities else 'Wszystkie'}",
                f"• Max budżet: {f'{p.budget_max:.0f} PLN/os.' if p.budget_max else 'Bez limitu'}",
                f"• Min gwiazdki: {f'{p.hotel_stars_min:.0f}★' if p.hotel_stars_min else 'Brak constraint'}",
                f"• Długość pobytu: {p.duration_min or 1}-{p.duration_max or 14} nocy",
                f"• Wyżywienie: {', '.join(p.meal_types) if p.meal_types else 'Wszystkie'}",
                f"• Typ transportu: {', '.join(p.transport_types) if p.transport_types else 'Wszystkie'}",
            ]
            await self._send_reply(chat_id, "\n".join(lines))

    async def _cmd_edit_profile(self, chat_id: int | str, args: list[str]) -> None:
        """Edit a profile field directly via command line."""
        if len(args) < 2 or "=" not in args[1]:
            await self._send_reply(
                chat_id,
                "❓ Format polecenia:\n<code>/edit_profile [nr_profilu] [pole=wartość]</code>\n"
                "Przykłady:\n"
                "• <code>/edit_profile 1 budget_max=3500</code>\n"
                "• <code>/edit_profile 1 name=Egipt Super LastMinute</code>",
            )
            return

        prof_target = args[0]
        field_assignment = " ".join(args[1:])
        field_name, field_val = [x.strip() for x in field_assignment.split("=", 1)]

        async with async_session_factory() as session:
            p = await self._resolve_profile_by_index_or_id(session, prof_target)
            if not p:
                await self._send_reply(chat_id, f"❌ Nie znaleziono profilu pasującego do: <b>{prof_target}</b>")
                return

            if field_name in ("budget_max", "budget_min"):
                try:
                    setattr(p, field_name, Decimal(field_val))
                except Exception:
                    await self._send_reply(chat_id, f"❌ Niepoprawna kwota: {field_val}")
                    return
            elif field_name in ("duration_min", "duration_max", "adults", "children"):
                try:
                    setattr(p, field_name, int(field_val))
                except Exception:
                    await self._send_reply(chat_id, f"❌ Niepoprawna liczba: {field_val}")
                    return
            elif field_name == "name":
                p.name = field_val
            elif field_name == "notification_policy":
                if field_val in _POLICY_LABELS:
                    p.notification_policy = field_val
                else:
                    await self._send_reply(chat_id, f"❌ Dostępne polityki: {', '.join(_POLICY_LABELS.keys())}")
                    return
            else:
                await self._send_reply(chat_id, f"❌ Pole {field_name} nie obsługuje edycji z komendy. Edytuj w serwisie WWW.")
                return

            await session.commit()
            p_name = p.name

        await self._send_reply(chat_id, f"✅ Zaktualizowano profil <b>{p_name}</b>: {field_name} ➔ {field_val}")

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

            transport_badge = _TRANSPORT_ICONS.get(str(o.transport_type or "flight").lower(), "✈️ Przelot")
            clean_url = build_direct_offer_url(o.provider, str(o.external_id or o.id), o.offer_url) or o.offer_url

            lines.append(
                f"{idx}. 🏨 <b>{o.hotel_name}</b>{stars}\n"
                f"   📍 {o.country}{region_str}\n"
                f"   📅 {o.departure_date} ({o.duration_nights} nocy) | {transport_badge} (Wylot: {o.departure_city})\n"
                f"   🍽️ {o.meal_type} | {people_str}\n"
                f"   💰 <b>{o.price_per_person:.0f} PLN/os.</b>{total_str}{score}\n"
                f"   🔗 <a href=\"{clean_url}\">Otwórz ofertę w {o.provider.upper()}</a>\n"
            )

        await self._send_reply(chat_id, "\n".join(lines))


# Singleton instance
telegram_bot_listener = TelegramBotListener()
