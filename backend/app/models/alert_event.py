"""Alert event model — records noteworthy events for notification dispatch."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AlertEvent(Base):
    """A single alert-worthy event detected by the Alert Engine.

    The Alert Engine creates AlertEvent rows; the Notification Service
    reads them and dispatches messages (e.g. Telegram). This separation
    ensures alerting logic is independent of delivery channel.
    """

    __tablename__ = "alert_events"

    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="CASCADE"),
        nullable=False,
    )
    profile_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("travel_profiles.id", ondelete="SET NULL"),
        nullable=True,
    )
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[str] = mapped_column(String(1000), nullable=False)
    priority_score: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    priority_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reasons_json: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    offer: Mapped["Offer"] = relationship(lazy="selectin")
    profile: Mapped["TravelProfile | None"] = relationship(
        back_populates="alert_events", lazy="selectin"
    )

    __table_args__ = (
        Index("ix_alert_event_offer_id", "offer_id"),
        Index("ix_alert_event_profile_id", "profile_id"),
        Index("ix_alert_event_alert_type", "alert_type"),
        Index("ix_alert_event_is_read", "is_read"),
        Index("ix_alert_event_triggered_at", "triggered_at"),
    )

    def __repr__(self) -> str:
        return f"<AlertEvent {self.alert_type} offer={self.offer_id}>"


from app.models.offer import Offer  # noqa: E402, F401
from app.models.travel_profile import TravelProfile  # noqa: E402, F401
