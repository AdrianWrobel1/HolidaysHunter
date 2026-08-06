"""Alert Cooldown Policy — prevents notification spam when scanner runs continuously.

Suppresses repetitive alerts for the same offer/profile within a cooldown window,
unless explicit bypass triggers (price drop, priority upgrade, score jump, new min) occur.
"""

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist import AlertTimeline

logger = logging.getLogger(__name__)

DEFAULT_COOLDOWN_HOURS = 24
MIN_PRICE_DROP_BYPASS_PCT = 5.0
MIN_SCORE_JUMP_BYPASS_PTS = 10.0

# Priority ordering for upgrade checks
_LEVEL_RANK = {
    "LOW": 1,
    "NORMAL": 2,
    "HIGH": 3,
    "MUST_SEE": 4,
}


async def evaluate_cooldown_policy(
    session: AsyncSession,
    *,
    offer_id: UUID,
    profile_id: UUID | None,
    current_priority_score: float,
    current_priority_level: str,
    current_price: Decimal | float,
    current_deal_score: int | None = None,
    is_lowest_price: bool = False,
    cooldown_hours: int = DEFAULT_COOLDOWN_HOURS,
) -> tuple[bool, str]:
    """Evaluate whether alert notification should be dispatched or suppressed by cooldown.

    Returns:
        (should_send: bool, reason: str)
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)

    stmt = (
        select(AlertTimeline)
        .where(
            AlertTimeline.offer_id == offer_id,
            AlertTimeline.notification_status == "sent",
            AlertTimeline.timestamp >= cutoff,
        )
        .order_by(AlertTimeline.timestamp.desc())
        .limit(1)
    )
    if profile_id:
        stmt = stmt.where(AlertTimeline.profile_id == profile_id)

    res = await session.execute(stmt)
    last_sent = res.scalar_one_or_none()

    if not last_sent:
        return True, "No recent alert sent within cooldown window"

    # Evaluate bypass triggers:
    # 1. New historical lowest price
    if is_lowest_price:
        return True, "Bypass cooldown: New historical minimum price"

    # 2. Priority level upgrade
    old_rank = _LEVEL_RANK.get(last_sent.priority_level, 1)
    new_rank = _LEVEL_RANK.get(current_priority_level, 1)
    if new_rank > old_rank:
        return True, f"Bypass cooldown: Priority upgrade ({last_sent.priority_level} -> {current_priority_level})"

    # 3. Significant price drop (>= 5%)
    if last_sent.price_per_person and float(last_sent.price_per_person) > 0:
        prev_p = float(last_sent.price_per_person)
        curr_p = float(current_price)
        if curr_p < prev_p:
            drop_pct = ((prev_p - curr_p) / prev_p) * 100.0
            if drop_pct >= MIN_PRICE_DROP_BYPASS_PCT:
                return True, f"Bypass cooldown: Significant price drop ({drop_pct:.1f}%)"

    # 4. Significant Deal Score jump (>= 10 pts)
    if current_deal_score is not None and last_sent.deal_score is not None:
        if (current_deal_score - last_sent.deal_score) >= MIN_SCORE_JUMP_BYPASS_PTS:
            return True, f"Bypass cooldown: Deal score jump ({last_sent.deal_score} -> {current_deal_score})"

    # 5. Significant Priority Score jump (>= 10 pts)
    if (current_priority_score - float(last_sent.priority_score)) >= MIN_SCORE_JUMP_BYPASS_PTS:
        return True, f"Bypass cooldown: Priority score jump (+{current_priority_score - float(last_sent.priority_score):.1f} pts)"

    return False, f"Cooldown active (last alert sent at {last_sent.timestamp.strftime('%H:%M')})"
