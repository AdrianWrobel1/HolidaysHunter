"""Travel Score Engine — calculates offer attractiveness on a 0-100 scale.

Score components:
  - Price value     (0-25): price per person per night relative to market
  - Price trend     (0-20): historical price drops
  - Hotel quality   (0-25): stars + guest rating
  - Meal quality    (0-15): all-inclusive > self-catering
  - Profile match   (0-15): bonus for matching user profiles
"""

import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import AlertType, MealType
from app.models.offer import Offer
from app.models.price_history import PriceHistory
from app.models.travel_profile import TravelProfile

logger = logging.getLogger(__name__)

# Meal type quality scores (out of 15)
_MEAL_SCORES: dict[str, int] = {
    MealType.ALL_INCLUSIVE: 15,
    MealType.FULL_BOARD: 12,
    MealType.HALF_BOARD: 8,
    MealType.BED_AND_BREAKFAST: 4,
    MealType.SELF_CATERING: 0,
}


def calculate_travel_score(
    offer: Offer,
    profiles: list[TravelProfile],
) -> int:
    """Calculate the Travel Score (0-100) for a single offer.

    Higher scores indicate more attractive deals. The score is deterministic
    given the same inputs, so it can be recalculated at any time.
    """
    score = 0.0

    # --- Price value (0-25) ---
    score += _score_price_value(offer)

    # --- Price trend (0-20) ---
    score += _score_price_trend(offer)

    # --- Hotel quality (0-25) ---
    score += _score_hotel_quality(offer)

    # --- Meal quality (0-15) ---
    score += _score_meal_quality(offer)

    # --- Profile match (0-15) ---
    score += _score_profile_match(offer, profiles)

    return min(100, max(0, round(score)))


def _score_price_value(offer: Offer) -> float:
    """Score based on price per person per night. Lower = better.

    Benchmarks (PLN per person per night):
      <= 150  → 25 points (excellent deal)
      <= 250  → 20 points (good deal)
      <= 400  → 15 points (average)
      <= 600  → 10 points (above average)
      > 600   → 5 points (expensive)
    """
    if offer.duration_nights <= 0:
        return 5.0

    ppn = float(offer.price_per_person) / offer.duration_nights

    if ppn <= 150:
        return 25.0
    if ppn <= 250:
        return 20.0
    if ppn <= 400:
        return 15.0
    if ppn <= 600:
        return 10.0
    return 5.0


def _score_price_trend(offer: Offer) -> float:
    """Score based on price history — reward significant drops.

    Up to 20 points for price drops of 30%+.
    """
    if not offer.price_history or len(offer.price_history) < 2:
        return 0.0

    sorted_history = sorted(offer.price_history, key=lambda ph: ph.recorded_at)
    first_price = float(sorted_history[0].price_per_person)
    current_price = float(sorted_history[-1].price_per_person)

    if first_price <= 0:
        return 0.0

    change_pct = (current_price - first_price) / first_price * 100

    if change_pct >= 0:
        return 0.0

    drop_pct = abs(change_pct)
    # Scale: 5% drop → 3pts, 10% → 7pts, 20% → 13pts, 30%+ → 20pts
    return min(20.0, drop_pct * 0.67)


def _score_hotel_quality(offer: Offer) -> float:
    """Score based on hotel stars (0-15) and guest rating (0-10).

    Stars: 5★ → 15, 4★ → 12, 3★ → 9
    Rating: 9+ → 10, 8+ → 8, 7+ → 5, below → 2
    """
    score = 0.0

    if offer.hotel_stars is not None:
        score += min(15.0, float(offer.hotel_stars) * 3.0)

    if offer.hotel_rating is not None:
        rating = float(offer.hotel_rating)
        if rating >= 9.0:
            score += 10.0
        elif rating >= 8.0:
            score += 8.0
        elif rating >= 7.0:
            score += 5.0
        else:
            score += 2.0

    return score


def _score_meal_quality(offer: Offer) -> float:
    """Score based on meal type."""
    return float(_MEAL_SCORES.get(offer.meal_type, 0))


def _score_profile_match(offer: Offer, profiles: list[TravelProfile]) -> float:
    """Bonus points if offer matches any active travel profile."""
    for profile in profiles:
        if offer_matches_profile(offer, profile):
            return 15.0
    return 0.0


def offer_matches_profile(offer: Offer, profile: TravelProfile) -> bool:
    """Check whether an offer satisfies all criteria of a travel profile.

    Each profile field is a constraint. Null/empty means "no constraint".
    All non-null constraints must be satisfied (AND logic).
    """
    if not profile.is_active:
        return False

    if profile.countries and offer.country not in profile.countries:
        return False

    if profile.regions and offer.region not in profile.regions:
        return False

    if profile.departure_cities and offer.departure_city not in profile.departure_cities:
        return False

    if profile.date_from and offer.departure_date < profile.date_from:
        return False

    if profile.date_to and offer.departure_date > profile.date_to:
        return False

    if profile.duration_min is not None and offer.duration_nights < profile.duration_min:
        return False

    if profile.duration_max is not None and offer.duration_nights > profile.duration_max:
        return False

    if profile.budget_min is not None and offer.price_per_person < profile.budget_min:
        return False

    if profile.budget_max is not None and offer.price_per_person > profile.budget_max:
        return False

    if profile.adults is not None and offer.adults != profile.adults:
        return False

    if profile.children is not None and offer.children != profile.children:
        return False

    if profile.hotel_stars_min is not None and (
        offer.hotel_stars is None or offer.hotel_stars < float(profile.hotel_stars_min)
    ):
        return False

    if profile.meal_types and offer.meal_type not in profile.meal_types:
        return False

    if profile.providers and offer.provider not in profile.providers:
        return False

    return True


async def recalculate_scores(
    offers: list[Offer],
    session: AsyncSession,
) -> None:
    """Recalculate travel scores for a batch of offers.

    Called after each import run to update scores with fresh data.
    """
    profiles_result = await session.execute(
        select(TravelProfile).where(TravelProfile.is_active.is_(True))
    )
    profiles = list(profiles_result.scalars().all())

    for offer in offers:
        offer.travel_score = calculate_travel_score(offer, profiles)

    logger.info("Recalculated scores for %d offers", len(offers))
