"""Travel profile service — CRUD operations for travel profiles."""

import logging
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.travel_profile import TravelProfile

logger = logging.getLogger(__name__)


async def get_profiles(
    session: AsyncSession,
    *,
    active_only: bool = True,
) -> list[TravelProfile]:
    """List all travel profiles."""
    stmt = select(TravelProfile).order_by(TravelProfile.created_at.desc())
    if active_only:
        stmt = stmt.where(TravelProfile.is_active.is_(True))
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_profile(
    profile_id: UUID,
    session: AsyncSession,
) -> TravelProfile | None:
    """Get a single travel profile by ID."""
    stmt = select(TravelProfile).where(TravelProfile.id == profile_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def create_profile(
    session: AsyncSession,
    *,
    name: str,
    countries: list[str] | None = None,
    regions: list[str] | None = None,
    departure_cities: list[str] | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    duration_min: int | None = None,
    duration_max: int | None = None,
    budget_min: Decimal | None = None,
    budget_max: Decimal | None = None,
    adults: int | None = None,
    children: int | None = None,
    hotel_stars_min: float | None = None,
    meal_types: list[str] | None = None,
    providers: list[str] | None = None,
) -> TravelProfile:
    """Create a new travel profile."""
    profile = TravelProfile(
        name=name,
        countries=countries,
        regions=regions,
        departure_cities=departure_cities,
        date_from=date_from,
        date_to=date_to,
        duration_min=duration_min,
        duration_max=duration_max,
        budget_min=budget_min,
        budget_max=budget_max,
        adults=adults,
        children=children,
        hotel_stars_min=hotel_stars_min,
        meal_types=meal_types,
        providers=providers,
        is_active=True,
    )
    session.add(profile)
    await session.flush()
    logger.info("Created travel profile: %s (id=%s)", name, profile.id)
    return profile


async def update_profile(
    profile_id: UUID,
    session: AsyncSession,
    **fields,
) -> TravelProfile | None:
    """Update an existing travel profile. Only provided fields are changed."""
    profile = await get_profile(profile_id, session)
    if profile is None:
        return None

    allowed_fields = {
        "name", "countries", "regions", "departure_cities",
        "date_from", "date_to", "duration_min", "duration_max",
        "budget_min", "budget_max", "adults", "children",
        "hotel_stars_min", "meal_types", "providers", "is_active",
    }

    for key, value in fields.items():
        if key in allowed_fields:
            setattr(profile, key, value)

    await session.flush()
    logger.info("Updated travel profile: %s (id=%s)", profile.name, profile.id)
    return profile


async def delete_profile(
    profile_id: UUID,
    session: AsyncSession,
) -> bool:
    """Delete a travel profile. Returns True if profile existed."""
    profile = await get_profile(profile_id, session)
    if profile is None:
        return False

    await session.delete(profile)
    await session.flush()
    logger.info("Deleted travel profile: id=%s", profile_id)
    return True
