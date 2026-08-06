"""Completeness score component for Deal Score."""

from app.analysis_framework.context import AnalysisContext
from app.analysis_framework.deal_score.base_component import (
    BaseScoreComponent,
    ComponentScoreResult,
)


class CompletenessScoreComponent(BaseScoreComponent):
    """Scores data completeness of the offer object."""

    name = "completeness_score"
    weight = 0.10

    def calculate(self, context: AnalysisContext) -> ComponentScoreResult:
        target = context.analyzed_object
        if not target:
            return ComponentScoreResult(
                name=self.name,
                score=0.0,
                weight=self.weight,
                weighted_score=0.0,
                explanation="Brak obiektu oferty.",
            )

        fields = [
            "title", "country", "region", "city", "hotel_name",
            "hotel_stars", "departure_date", "return_date",
            "departure_city", "meal_type", "price_per_person",
            "offer_url", "image_url"
        ]
        present = sum(1 for f in fields if getattr(target, f, None) is not None)
        pct = (present / len(fields)) * 100.0

        return ComponentScoreResult(
            name=self.name,
            score=pct,
            weight=self.weight,
            weighted_score=pct * self.weight,
            explanation=f"Wypełnienie pól oferty: {pct:.0f}% ({present}/{len(fields)}).",
        )
