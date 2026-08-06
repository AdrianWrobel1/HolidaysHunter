"""Similarity score component for Deal Score."""

from app.analysis_framework.context import AnalysisContext
from app.analysis_framework.deal_score.base_component import (
    BaseScoreComponent,
    ComponentScoreResult,
)


class SimilarityScoreComponent(BaseScoreComponent):
    """Scores how well this offer compares against close similarity matches."""

    name = "similarity_score"
    weight = 0.20

    def calculate(self, context: AnalysisContext) -> ComponentScoreResult:
        similarity = context.artifacts.get("similarity")
        if not similarity:
            return ComponentScoreResult(
                name=self.name,
                score=50.0,
                weight=self.weight,
                weighted_score=10.0,
                explanation="Brak danych o podobieństwie ofert.",
            )

        offers = similarity.get("similar_offers", [])
        if not offers:
            score = 50.0
            explanation = "Brak bliskich ofert porównawczych."
        else:
            top_scores = [o.get("similarity_score", 0) for o in offers[:5]]
            avg_top = sum(top_scores) / len(top_scores) if top_scores else 50
            score = float(avg_top)
            explanation = f"Znaleziono {len(offers)} podobnych ofert o średnim podobieństwie {score:.1f}%."

        return ComponentScoreResult(
            name=self.name,
            score=score,
            weight=self.weight,
            weighted_score=score * self.weight,
            explanation=explanation,
        )
