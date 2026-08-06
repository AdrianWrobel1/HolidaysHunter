"""Alert Timeline logging service — records every notification decision into database."""

import logging
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist import AlertTimeline

logger = logging.getLogger(__name__)


async def record_timeline_entry(
    session: AsyncSession,
    *,
    offer_id: UUID,
    profile_id: UUID | None = None,
    user_chat_id: str | None = None,
    priority_score: float,
    priority_level: str,
    reasons: list[str] | dict[str, Any] | None = None,
    price_per_person: Decimal | float,
    deal_score: int | None = None,
    value_score: float | Decimal | None = None,
    notification_status: str,  # 'sent', 'suppressed_cooldown', 'suppressed_policy', 'suppressed_ignored', 'watched_update'
) -> AlertTimeline:
    """Record an entry in the AlertTimeline table."""
    entry = AlertTimeline(
        offer_id=offer_id,
        profile_id=profile_id,
        user_chat_id=str(user_chat_id) if user_chat_id else None,
        priority_score=Decimal(str(round(priority_score, 2))),
        priority_level=str(priority_level),
        reasons=reasons,
        price_per_person=Decimal(str(price_per_person)),
        deal_score=deal_score,
        value_score=Decimal(str(round(float(value_score), 2))) if value_score is not None else None,
        notification_status=str(notification_status),
    )
    session.add(entry)
    logger.debug(
        "AlertTimeline logged: status=%s, priority=%s, offer=%s",
        notification_status, priority_level, offer_id,
    )
    return entry
