"""Watchlist & Ignore offer management service."""

import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist import OfferIgnore, OfferWatchlist

logger = logging.getLogger(__name__)

# Override thresholds for ignored offers
IGNORE_PRICE_DROP_OVERRIDE_PCT = 15.0
IGNORE_PRIORITY_JUMP_OVERRIDE_PTS = 20.0


async def add_to_watchlist(
    session: AsyncSession,
    user_chat_id: str,
    offer_id: UUID,
    current_price: Decimal | float | None = None,
    current_deal_score: int | None = None,
) -> bool:
    """Add an offer to user watchlist. Returns True if created/exists."""
    stmt = select(OfferWatchlist).where(
        OfferWatchlist.user_chat_id == str(user_chat_id),
        OfferWatchlist.offer_id == offer_id,
    )
    res = await session.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        if current_price is not None:
            existing.last_notified_price = Decimal(str(current_price))
        if current_deal_score is not None:
            existing.last_notified_deal_score = current_deal_score
        return True

    item = OfferWatchlist(
        user_chat_id=str(user_chat_id),
        offer_id=offer_id,
        last_notified_price=Decimal(str(current_price)) if current_price is not None else None,
        last_notified_deal_score=current_deal_score,
    )
    session.add(item)
    logger.info("Offer %s added to watchlist for chat %s", offer_id, user_chat_id)
    return True


async def remove_from_watchlist(
    session: AsyncSession,
    user_chat_id: str,
    offer_id: UUID,
) -> bool:
    """Remove an offer from user watchlist."""
    stmt = delete(OfferWatchlist).where(
        OfferWatchlist.user_chat_id == str(user_chat_id),
        OfferWatchlist.offer_id == offer_id,
    )
    res = await session.execute(stmt)
    return (res.rowcount or 0) > 0


async def is_offer_watched(
    session: AsyncSession,
    user_chat_id: str,
    offer_id: UUID,
) -> OfferWatchlist | None:
    """Check if offer is in user watchlist."""
    stmt = select(OfferWatchlist).where(
        OfferWatchlist.user_chat_id == str(user_chat_id),
        OfferWatchlist.offer_id == offer_id,
    )
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def ignore_offer(
    session: AsyncSession,
    user_chat_id: str,
    offer_id: UUID,
    priority_score: float | Decimal | None = None,
    price: float | Decimal | None = None,
) -> bool:
    """Ignore an offer to suppress notifications."""
    stmt = select(OfferIgnore).where(
        OfferIgnore.user_chat_id == str(user_chat_id),
        OfferIgnore.offer_id == offer_id,
    )
    res = await session.execute(stmt)
    existing = res.scalar_one_or_none()

    if existing:
        return True

    item = OfferIgnore(
        user_chat_id=str(user_chat_id),
        offer_id=offer_id,
        ignored_priority_score=Decimal(str(priority_score)) if priority_score is not None else None,
        ignored_price=Decimal(str(price)) if price is not None else None,
    )
    session.add(item)
    logger.info("Offer %s ignored for chat %s", offer_id, user_chat_id)
    return True


async def unignore_offer(
    session: AsyncSession,
    user_chat_id: str,
    offer_id: UUID,
) -> bool:
    """Un-ignore an offer."""
    stmt = delete(OfferIgnore).where(
        OfferIgnore.user_chat_id == str(user_chat_id),
        OfferIgnore.offer_id == offer_id,
    )
    res = await session.execute(stmt)
    return (res.rowcount or 0) > 0


async def is_offer_ignored(
    session: AsyncSession,
    user_chat_id: str,
    offer_id: UUID,
    current_priority_score: float | None = None,
    current_price: float | Decimal | None = None,
) -> tuple[bool, str | None]:
    """Check whether offer is ignored for user.

    Returns (is_ignored, override_reason).
    If an override rule triggers (major price drop or priority jump),
    returns (False, override_reason).
    """
    stmt = select(OfferIgnore).where(
        OfferIgnore.user_chat_id == str(user_chat_id),
        OfferIgnore.offer_id == offer_id,
    )
    res = await session.execute(stmt)
    ignore_rec = res.scalar_one_or_none()

    if not ignore_rec:
        return False, None

    # Check override rules:
    # 1. Price drop >= 15%
    if (
        current_price is not None
        and ignore_rec.ignored_price is not None
        and float(ignore_rec.ignored_price) > 0
    ):
        orig_p = float(ignore_rec.ignored_price)
        curr_p = float(current_price)
        if curr_p < orig_p:
            drop_pct = ((orig_p - curr_p) / orig_p) * 100.0
            if drop_pct >= IGNORE_PRICE_DROP_OVERRIDE_PCT:
                logger.info(
                    "Override ignore for offer %s: price drop %.1f%% >= %.1f%%",
                    offer_id, drop_pct, IGNORE_PRICE_DROP_OVERRIDE_PCT,
                )
                return False, f"Major price drop ({drop_pct:.1f}%) overridden"

    # 2. Priority jump >= 20 pts
    if (
        current_priority_score is not None
        and ignore_rec.ignored_priority_score is not None
    ):
        orig_score = float(ignore_rec.ignored_priority_score)
        if (current_priority_score - orig_score) >= IGNORE_PRIORITY_JUMP_OVERRIDE_PTS:
            logger.info(
                "Override ignore for offer %s: priority jump %.1f -> %.1f",
                offer_id, orig_score, current_priority_score,
            )
            return False, f"Priority score jump (+{current_priority_score - orig_score:.1f} pts) overridden"

    return True, None
