"""Market score component for Deal Score."""

from app.analysis_framework.context import AnalysisContext
from app.analysis_framework.deal_score.base_component import (
    BaseScoreComponent,
    ComponentScoreResult,
)


class MarketScoreComponent(BaseScoreComponent):
    """Scores offer position relative to market percentile rank."""

    name = "market_score"
    weight = 0.15

    def calculate(self, context: AnalysisContext) -> ComponentScoreResult:
        market_pos = context.artifacts.get("market_position")
        if not market_pos:
            return ComponentScoreResult(
                name=self.name,
                score=50.0,
                weight=self.weight,
                weighted_score=7.5,
                explanation="Brak danych o pozycji rynkowej.",
            )

        cheaper_than_pct = float(market_pos.get("cheaper_than_pct", 50))
        score = max(0.0, min(100.0, cheaper_than_pct))
        explanation = f"Oferta jest tańsza niż {cheaper_than_pct:.0f}% ofert rynkowych."

        return ComponentScoreResult(
            name=self.name,
            score=score,
            weight=self.weight,
            weighted_score=score * self.weight,
            explanation=explanation,
        )
