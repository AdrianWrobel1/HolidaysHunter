"""Season score component for Deal Score."""

from datetime import date
from app.analysis_framework.context import AnalysisContext
from app.analysis_framework.deal_score.base_component import (
    BaseScoreComponent,
    ComponentScoreResult,
)


class SeasonScoreComponent(BaseScoreComponent):
    """Scores offer seasonality attractiveness based on travel dates."""

    name = "season_score"
    weight = 0.10

    def calculate(self, context: AnalysisContext) -> ComponentScoreResult:
        target = context.analyzed_object
        dep_date = getattr(target, "departure_date", None)

        if not dep_date:
            score = 70.0
            explanation = "Brak specyfikacji daty wylotu."
        else:
            month = dep_date.month if isinstance(dep_date, date) else 6
            # Peak season (June-August, Dec) vs shoulder season
            if month in (6, 7, 8):
                score = 85.0
                explanation = "Szczyt sezonu letniego (wysokie zainteresowanie)."
            elif month in (5, 9, 10):
                score = 90.0
                explanation = "Optymalny sezon średni (dobra pogoda i atrakcyjna cena)."
            else:
                score = 65.0
                explanation = "Poza szczytem sezonu."

        return ComponentScoreResult(
            name=self.name,
            score=score,
            weight=self.weight,
            weighted_score=score * self.weight,
            explanation=explanation,
        )
