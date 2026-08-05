import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PriceHistory(Base):
    """Records a price snapshot each time an offer's price changes.

    A new row is inserted only when the price differs from the most recent
    recorded value, keeping the table lean while preserving full history.
    """

    __tablename__ = "price_history"

    offer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offers.id", ondelete="CASCADE"),
        nullable=False,
    )
    price_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_per_person: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    offer: Mapped["Offer"] = relationship(back_populates="price_history")

    __table_args__ = (
        Index("ix_price_history_offer_id", "offer_id"),
        Index("ix_price_history_recorded_at", "recorded_at"),
    )

    def __repr__(self) -> str:
        return f"<PriceHistory offer={self.offer_id} total={self.price_total} at={self.recorded_at}>"


from app.models.offer import Offer  # noqa: E402, F401
