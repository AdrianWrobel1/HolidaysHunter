"""Alerts API — list and manage alert events."""

import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import AlertEventResponse, AlertsListResponse
from app.database.session import get_session
from app.models.alert_event import AlertEvent

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


@router.get("", response_model=AlertsListResponse)
async def list_alerts_endpoint(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    alert_type: str | None = Query(None),
    unread_only: bool = Query(False),
    session: AsyncSession = Depends(get_session),
) -> AlertsListResponse:
    """List alert events with optional filtering."""
    stmt = select(AlertEvent)

    if unread_only:
        stmt = stmt.where(AlertEvent.is_read.is_(False))
    if alert_type:
        stmt = stmt.where(AlertEvent.alert_type == alert_type)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar_one()

    stmt = stmt.order_by(AlertEvent.triggered_at.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)

    result = await session.execute(stmt)
    alerts = result.scalars().all()

    return AlertsListResponse(
        alerts=[AlertEventResponse.model_validate(a) for a in alerts],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size) if total > 0 else 0,
    )


@router.patch("/{alert_id}/read", response_model=AlertEventResponse)
async def mark_alert_read_endpoint(
    alert_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> AlertEventResponse:
    """Mark a single alert as read."""
    stmt = select(AlertEvent).where(AlertEvent.id == alert_id)
    result = await session.execute(stmt)
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    await session.flush()
    return AlertEventResponse.model_validate(alert)


@router.post("/read-all", status_code=204)
async def mark_all_alerts_read_endpoint(
    session: AsyncSession = Depends(get_session),
) -> None:
    """Mark all unread alerts as read."""
    stmt = (
        update(AlertEvent)
        .where(AlertEvent.is_read.is_(False))
        .values(is_read=True)
    )
    await session.execute(stmt)
    await session.flush()


@router.get("/telegram/status")
async def get_telegram_status_endpoint() -> dict:
    """Get current Telegram notification toggle status."""
    from app.notifications.telegram import TelegramChannel
    return {
        "enabled": TelegramChannel.get_enabled(),
        "configured": bool(TelegramChannel()._bot_token and TelegramChannel()._chat_id),
    }


@router.post("/telegram/toggle")
async def toggle_telegram_endpoint(enabled: bool = Query(...)) -> dict:
    """Enable or disable Telegram notifications globally."""
    from app.notifications.telegram import TelegramChannel
    TelegramChannel.set_enabled(enabled)
    return {
        "status": "success",
        "enabled": TelegramChannel.get_enabled(),
        "message": f"Powiadomienia Telegram zostały {'włączone' if enabled else 'wyłączone'}.",
    }
