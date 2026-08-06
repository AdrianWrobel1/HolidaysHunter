"""Quality score component for Deal Score."""

from app.analysis_framework.context import AnalysisContext
from app.analysis_framework.deal_score.base_component import (
    BaseScoreComponent,
    ComponentScoreResult,
)


class QualityScoreComponent(BaseScoreComponent):
    """Scores offer quality based on hotel stars and guest rating."""

    name = "quality_score"
    weight = 0.15

    def calculate(self, context: AnalysisContext) -> ComponentScoreResult:
        quality_data = context.artifacts.get("offer_quality")
        if quality_data and "quality_score" in quality_data:
            score = float(quality_data["quality_score"])
            explanation = f"Wskaźnik jakości oferty wynosi {score:.0f}/100."
        else:
            target = context.analyzed_object
            stars = float(getattr(target, "hotel_stars", 0) or 3)
            rating = float(getattr(target, "hotel_rating", 0) or 7.5)
            score = min(100.0, (stars * 12.0) + (rating * 4.0))
            explanation = f"Standard hotelu: {stars} gwiazdek, ocena gości: {rating}."

        return ComponentScoreResult(
            name=self.name,
            score=score,
            weight=self.weight,
            weighted_score=score * self.weight,
            explanation=explanation,
        )
