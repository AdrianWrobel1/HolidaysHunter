"""Default configuration and feature weights for Similarity Engine."""

# Weights for multi-feature similarity scoring (sum to 1.0)
DEFAULT_SIMILARITY_WEIGHTS: dict[str, float] = {
    "hotel_name": 0.25,
    "country": 0.15,
    "region": 0.10,
    "city": 0.05,
    "hotel_stars": 0.08,
    "duration_nights": 0.07,
    "departure_date": 0.10,
    "meal_type": 0.08,
    "departure_city": 0.05,
    "price": 0.07,
}
