from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.enums import MealType, Provider, TransportType


class Offer(Base):
    """Normalized travel offer from any provider.

    The unique constraint on (provider, external_id, departure_date,
    departure_city, adults, children) identifies the same bookable product
    across successive imports so we can track price changes.
    """

    __tablename__ = "offers"

    # Provider identification
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)

    # Destination
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str | None] = mapped_column(String(200), nullable=True)
    city: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Hotel
    hotel_name: Mapped[str] = mapped_column(String(500), nullable=False)
    hotel_stars: Mapped[float | None] = mapped_column(Numeric(2, 1), nullable=True)
    hotel_rating: Mapped[float | None] = mapped_column(Numeric(3, 1), nullable=True)

    # Travel dates
    departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[date] = mapped_column(Date, nullable=False)
    duration_nights: Mapped[int] = mapped_column(Integer, nullable=False)

    # Departure
    departure_city: Mapped[str] = mapped_column(String(100), nullable=False)

    # Travelers
    adults: Mapped[int] = mapped_column(Integer, nullable=False)
    children: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Offer details
    meal_type: Mapped[str] = mapped_column(String(50), nullable=False)
    transport_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # Pricing
    price_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price_per_person: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="PLN")

    # Links
    offer_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    image_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Scoring
    travel_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Status
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    price_history: Mapped[list["PriceHistory"]] = relationship(
        back_populates="offer",
        cascade="all, delete-orphan",
        order_by="PriceHistory.recorded_at",
        lazy="selectin",
    )

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "external_id",
            "departure_date",
            "departure_city",
            "adults",
            "children",
            name="uq_offer_identity",
        ),
        Index("ix_offer_provider", "provider"),
        Index("ix_offer_country", "country"),
        Index("ix_offer_departure_date", "departure_date"),
        Index("ix_offer_price_per_person", "price_per_person"),
        Index("ix_offer_travel_score", "travel_score"),
        Index("ix_offer_is_available", "is_available"),
    )

    def __repr__(self) -> str:
        return (
            f"<Offer {self.provider}:{self.external_id} "
            f"{self.hotel_name} {self.departure_date}>"
        )


# Avoid circular import — PriceHistory is imported at module level for the relationship string ref.
from app.models.price_history import PriceHistory  # noqa: E402, F401
