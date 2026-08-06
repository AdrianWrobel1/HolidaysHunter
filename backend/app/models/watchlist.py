"""Models for Watchlist, Ignore list, and Alert Timeline persistence."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class OfferWatchlist(Base):
    """User-tracked offer watchlist.

    When an offer is saved to the watchlist, full alert spam is suppressed
    and only meaningful updates (price drop, deal score jump) trigger notifications.
    """

    __tablename__ = "offer_watchlists"

    user_chat_id: Mapped[str] = mapped_column(String(100), nullable=False)
    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="CASCADE"),
        nullable=False,
    )
    last_notified_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    last_notified_deal_score: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    offer: Mapped["Offer"] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_chat_id", "offer_id", name="uq_user_watchlist_offer"),
        Index("ix_offer_watchlists_user_chat_id", "user_chat_id"),
        Index("ix_offer_watchlists_offer_id", "offer_id"),
    )

    def __repr__(self) -> str:
        return f"<OfferWatchlist chat={self.user_chat_id} offer={self.offer_id}>"


class OfferIgnore(Base):
    """User-ignored offers.

    Suppresses all standard alert notifications for this offer unless a major
    price drop (>= 15%) or Priority Score jump (+20 pts) occurs.
    """

    __tablename__ = "offer_ignores"

    user_chat_id: Mapped[str] = mapped_column(String(100), nullable=False)
    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="CASCADE"),
        nullable=False,
    )
    ignored_priority_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    ignored_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    ignored_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    offer: Mapped["Offer"] = relationship(lazy="selectin")

    __table_args__ = (
        UniqueConstraint("user_chat_id", "offer_id", name="uq_user_ignore_offer"),
        Index("ix_offer_ignores_user_chat_id", "user_chat_id"),
        Index("ix_offer_ignores_offer_id", "offer_id"),
    )

    def __repr__(self) -> str:
        return f"<OfferIgnore chat={self.user_chat_id} offer={self.offer_id}>"


class AlertTimeline(Base):
    """Complete audit log of every alert evaluation & delivery decision.

    Records whether an alert was sent, suppressed by cooldown, suppressed by policy,
    suppressed by ignore list, or delivered as a watchlist update.
    """

    __tablename__ = "alert_timeline"

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
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
    user_chat_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    priority_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    priority_level: Mapped[str] = mapped_column(String(50), nullable=False)
    reasons: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    price_per_person: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    deal_score: Mapped[int | None] = mapped_column(nullable=True)
    value_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    notification_status: Mapped[str] = mapped_column(String(50), nullable=False)

    offer: Mapped["Offer"] = relationship(lazy="selectin")
    profile: Mapped["TravelProfile | None"] = relationship(lazy="selectin")

    __table_args__ = (
        Index("ix_alert_timeline_timestamp", "timestamp"),
        Index("ix_alert_timeline_offer_id", "offer_id"),
        Index("ix_alert_timeline_profile_id", "profile_id"),
        Index("ix_alert_timeline_notification_status", "notification_status"),
    )

    def __repr__(self) -> str:
        return f"<AlertTimeline status={self.notification_status} priority={self.priority_level} offer={self.offer_id}>"


from app.models.offer import Offer  # noqa: E402, F401
from app.models.travel_profile import TravelProfile  # noqa: E402, F401
