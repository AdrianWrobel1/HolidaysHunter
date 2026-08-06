"""Season component for Deal Score Engine."""

from datetime import date
from typing import Any
from app.scoring.base_component import BaseScoringComponent
from app.scoring.models import ComponentResult


class SeasonComponent(BaseScoringComponent):
    """Evaluates travel seasonality attractiveness."""

    name = "season"
    label = "Atrakcyjność Sezonowa"
    weight = 0.15

    def calculate(self, offer: Any, context: dict[str, Any] | None = None) -> ComponentResult:
        dep_date = getattr(offer, "departure_date", None)
        if not dep_date:
            raw_score = 70.0
            explanation = "Brak specyfikacji daty wyjazdu."
        else:
            month = dep_date.month if isinstance(dep_date, date) else 6
            if month in (5, 9, 10):
                raw_score = 95.0
                explanation = "Optymalny sezon średni — idealny stosunek pogody do ceny."
            elif month in (6, 7, 8):
                raw_score = 80.0
                explanation = "Szczyt sezonu wakacyjnego (wysoki popyt rynkowy)."
            else:
                raw_score = 65.0
                explanation = "Wyjazd poza szczytowym sezonem turystycznym."

        weighted_score = raw_score * self.weight
        impact = (raw_score - 50.0) * self.weight

        return ComponentResult(
            name=self.name,
            label=self.label,
            score=round(raw_score, 1),
            weight=self.weight,
            weighted_score=round(weighted_score, 2),
            impact=round(impact, 2),
            explanation=explanation,
        )
