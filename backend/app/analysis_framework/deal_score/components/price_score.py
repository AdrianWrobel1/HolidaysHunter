"""Price score component for Deal Score."""

from app.analysis_framework.context import AnalysisContext
from app.analysis_framework.deal_score.base_component import (
    BaseScoreComponent,
    ComponentScoreResult,
)


class PriceScoreComponent(BaseScoreComponent):
    """Scores offer price relative to market statistics."""

    name = "price_score"
    weight = 0.30

    def calculate(self, context: AnalysisContext) -> ComponentScoreResult:
        stats = context.artifacts.get("statistics")
        target = context.analyzed_object

        if not stats or not target:
            return ComponentScoreResult(
                name=self.name,
                score=50.0,
                weight=self.weight,
                weighted_score=15.0,
                explanation="Brak wystarczających danych statystycznych cen do pełnej oceny.",
            )

        mean_price = stats.get("mean_price_per_person", 0)
        curr_price = float(getattr(target, "price_per_person", 0))

        if mean_price <= 0 or curr_price <= 0:
            score = 50.0
        else:
            diff_pct = ((curr_price - mean_price) / mean_price) * 100
            # If price is 30% below mean -> 100, if equal -> 50, if 30% above -> 0
            score = max(0.0, min(100.0, 50.0 - (diff_pct * 1.67)))

        explanation = f"Cena za osobę wynosi {curr_price:.0f} PLN (średnia rynkowa: {mean_price:.0f} PLN)."

        return ComponentScoreResult(
            name=self.name,
            score=score,
            weight=self.weight,
            weighted_score=score * self.weight,
            explanation=explanation,
        )
