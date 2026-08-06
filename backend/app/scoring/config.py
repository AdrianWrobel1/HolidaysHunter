"""Default configuration, weights, and thresholds for the scoring system."""

from app.scoring.models import RankingProfile

# Value Engine Component Weights (Sum = 1.0)
DEFAULT_VALUE_WEIGHTS: dict[str, float] = {
    "hotel_quality": 0.30,
    "price_efficiency": 0.30,
    "meal_value": 0.15,
    "duration_value": 0.15,
    "transport_value": 0.10,
}

# Deal Score Component Weights (Sum = 1.0)
DEFAULT_DEAL_SCORE_WEIGHTS: dict[str, float] = {
    "value_score": 0.35,
    "market_position": 0.25,
    "season": 0.15,
    "completeness": 0.15,
    "availability": 0.10,
}

# Ranking Profile Weight Mixes
RANKING_PROFILE_CONFIGS: dict[RankingProfile, dict[str, float]] = {
    RankingProfile.BEST_DEALS: {
        "deal_score": 0.60,
        "value_score": 0.25,
        "confidence": 0.15,
    },
    RankingProfile.BEST_VALUE: {
        "deal_score": 0.25,
        "value_score": 0.65,
        "hotel_rating": 0.10,
    },
    RankingProfile.BUDGET: {
        "price_per_person": 0.50,
        "deal_score": 0.30,
        "value_score": 0.20,
    },
    RankingProfile.LUXURY: {
        "hotel_stars": 0.40,
        "guest_rating": 0.30,
        "value_score": 0.30,
    },
    RankingProfile.FAMILY: {
        "meal_type": 0.35,
        "value_score": 0.35,
        "hotel_stars": 0.30,
    },
    RankingProfile.BEACH: {
        "value_score": 0.40,
        "hotel_rating": 0.35,
        "deal_score": 0.25,
    },
    RankingProfile.LAST_MINUTE: {
        "deal_score": 0.45,
        "departure_proximity": 0.35,
        "value_score": 0.20,
    },
}
