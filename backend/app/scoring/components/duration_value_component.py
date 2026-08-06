"""Duration Value component for Value Engine."""

from typing import Any
from app.scoring.base_component import BaseScoringComponent
from app.scoring.models import ComponentResult


class DurationValueComponent(BaseScoringComponent):
    """Evaluates trip duration economy (longer stays reduce fixed transport/overhead cost per day)."""

    name = "duration_value"
    label = "Długość Pobytu i Atrakcyjność Dni"
    weight = 0.15

    def calculate(self, offer: Any, context: dict[str, Any] | None = None) -> ComponentResult:
        nights = int(getattr(offer, "duration_nights", 7) or 7)

        # Baseline: 7 nights = 70 pts, 10-14 nights = 90-100 pts, < 5 nights = 40-50 pts
        if nights >= 14:
            raw_score = 100.0
        elif nights >= 10:
            raw_score = 90.0
        elif nights >= 7:
            raw_score = 75.0
        elif nights >= 5:
            raw_score = 60.0
        else:
            raw_score = 40.0

        weighted_score = raw_score * self.weight
        impact = (raw_score - 50.0) * self.weight

        explanation = f"Pobyt obejmuje {nights} noclegów."

        return ComponentResult(
            name=self.name,
            label=self.label,
            score=round(raw_score, 1),
            weight=self.weight,
            weighted_score=round(weighted_score, 2),
            impact=round(impact, 2),
            explanation=explanation,
        )
