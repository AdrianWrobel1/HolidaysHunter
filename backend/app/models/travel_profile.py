"""Travel profile model — saved search criteria for automated monitoring."""

from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class TravelProfile(Base):
    """A saved set of search criteria that the system monitors automatically.

    Nullable fields mean "any value is acceptable".
    Array fields use PostgreSQL ARRAY(String) for efficient containment queries.
    """

    __tablename__ = "travel_profiles"

    # Identity
    name: Mapped[str] = mapped_column(String(200), nullable=False)

    # Destination criteria
    countries: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)), nullable=True
    )
    regions: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(200)), nullable=True
    )

    # Departure
    departure_cities: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(100)), nullable=True
    )

    # Date range
    date_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_to: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Duration (nights)
    duration_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_max: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Budget (per person)
    budget_min: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    budget_max: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)

    # Travelers
    adults: Mapped[int | None] = mapped_column(Integer, nullable=True)
    children: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Hotel standard
    hotel_stars_min: Mapped[float | None] = mapped_column(Numeric(2, 1), nullable=True)

    # Meal types (multiple allowed)
    meal_types: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), nullable=True
    )

    # Providers (multiple allowed)
    providers: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), nullable=True
    )

    # Transport types (multiple allowed)
    transport_types: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(50)), nullable=True
    )

    # Notification Policy: MUST_SEE_ONLY, HIGH_AND_MUST_SEE, ALL_ALERTS, DAILY_DIGEST
    notification_policy: Mapped[str] = mapped_column(
        String(50), nullable=False, default="HIGH_AND_MUST_SEE"
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Relationships
    alert_events: Mapped[list["AlertEvent"]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<TravelProfile {self.name} active={self.is_active}>"


from app.models.alert_event import AlertEvent  # noqa: E402, F401
