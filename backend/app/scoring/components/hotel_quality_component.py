"""Hotel Quality component for Value Engine."""

from typing import Any
from app.scoring.base_component import BaseScoringComponent
from app.scoring.models import ComponentResult


class HotelQualityComponent(BaseScoringComponent):
    """Evaluates hotel star standard and verified guest rating relative to baseline."""

    name = "hotel_quality"
    label = "Jakość i Standard Hotelu"
    weight = 0.30

    def calculate(self, offer: Any, context: dict[str, Any] | None = None) -> ComponentResult:
        stars = float(getattr(offer, "hotel_stars", 0) or 3.0)
        rating = float(getattr(offer, "hotel_rating", 0) or 7.5)

        # Stars contribution: max 50 pts (10 pts per star)
        star_pts = min(50.0, stars * 10.0)
        # Rating contribution: max 50 pts (5 pts per rating point out of 10)
        rating_pts = min(50.0, rating * 5.0)

        raw_score = max(0.0, min(100.0, star_pts + rating_pts))
        weighted_score = raw_score * self.weight
        # Impact relative to neutral 50 score
        impact = (raw_score - 50.0) * self.weight

        explanation = f"Standard hotelu ({stars:.1f}★) oraz opinie gości ({rating:.1f}/10)."

        return ComponentResult(
            name=self.name,
            label=self.label,
            score=round(raw_score, 1),
            weight=self.weight,
            weighted_score=round(weighted_score, 2),
            impact=round(impact, 2),
            explanation=explanation,
        )
