"""Value Score component for Deal Score Engine."""

from typing import Any
from app.scoring.base_component import BaseScoringComponent
from app.scoring.models import ComponentResult, ValueScore


class ValueScoreComponent(BaseScoringComponent):
    """Incorporates computed ValueScore into overall Deal Score."""

    name = "value_score"
    label = "Stosunek Jakości do Ceny (Value Score)"
    weight = 0.35

    def calculate(self, offer: Any, context: dict[str, Any] | None = None) -> ComponentResult:
        val_score_obj = (context or {}).get("value_score")
        if isinstance(val_score_obj, ValueScore):
            raw_score = float(val_score_obj.total_score)
        elif isinstance(val_score_obj, (int, float)):
            raw_score = float(val_score_obj)
        else:
            raw_score = 50.0

        weighted_score = raw_score * self.weight
        impact = (raw_score - 50.0) * self.weight

        explanation = f"Ocena wartości wyjazdu względem poniesionego kosztu: {raw_score:.0f}/100."

        return ComponentResult(
            name=self.name,
            label=self.label,
            score=round(raw_score, 1),
            weight=self.weight,
            weighted_score=round(weighted_score, 2),
            impact=round(impact, 2),
            explanation=explanation,
        )
