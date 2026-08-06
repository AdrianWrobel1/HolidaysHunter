"""Value Engine aggregating modular components to answer 'Ile rzeczywiście dostaję za swoje pieniądze?'"""

from typing import Any
from app.scoring.base_component import BaseScoringComponent
from app.scoring.components import (
    DurationValueComponent,
    HotelQualityComponent,
    MealValueComponent,
    PriceEfficiencyComponent,
    TransportValueComponent,
)
from app.scoring.explainability import ExplainabilityLayer
from app.scoring.models import ComponentResult, ValueScore


class ValueEngine:
    """Component-based Value Engine calculating independent ValueScore (0-100)."""

    def __init__(self, components: list[BaseScoringComponent] | None = None) -> None:
        self.components: list[BaseScoringComponent] = components or [
            HotelQualityComponent(),
            PriceEfficiencyComponent(),
            MealValueComponent(),
            DurationValueComponent(),
            TransportValueComponent(),
        ]

    def add_component(self, component: BaseScoringComponent) -> None:
        """Add a custom value component (e.g. WeatherValue, BeachQuality)."""
        self.components.append(component)

    def calculate(self, offer: Any, context: dict[str, Any] | None = None) -> ValueScore:
        """Calculate aggregated ValueScore across all registered components."""
        if not self.components:
            return ValueScore(
                total_score=50,
                raw_score=50.0,
                summary="Brak komponentów Value Engine.",
                components=[],
                explanations=[],
            )

        results: list[ComponentResult] = []
        total_weight = 0.0
        weighted_sum = 0.0

        for comp in self.components:
            res = comp.calculate(offer, context)
            results.append(res)
            total_weight += res.weight
            weighted_sum += res.weighted_score

        raw_score = (weighted_sum / total_weight) if total_weight > 0 else 50.0
        clamped_score = max(0.0, min(100.0, raw_score))
        final_score = int(round(clamped_score))

        explanations = ExplainabilityLayer.explain_value_score(clamped_score, results)
        summary = explanations[0] if explanations else "Wartość oferty."

        return ValueScore(
            total_score=final_score,
            raw_score=round(clamped_score, 2),
            summary=summary,
            components=results,
            explanations=explanations,
        )
