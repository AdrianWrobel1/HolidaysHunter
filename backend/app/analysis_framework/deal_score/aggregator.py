"""Deal Score Aggregator combining independent component scores into final 0-100 score."""

from dataclasses import dataclass, field
from typing import Any

from app.analysis_framework.context import AnalysisContext
from app.analysis_framework.deal_score.base_component import (
    BaseScoreComponent,
    ComponentScoreResult,
)


@dataclass
class AggregatedDealScore:
    """Final aggregated Deal Score result."""

    total_score: int  # 0-100 rounded
    raw_score: float
    components: dict[str, ComponentScoreResult] = field(default_factory=dict)
    summary: str = ""


class DealScoreAggregator:
    """Aggregates multiple score components into a unified 0-100 Deal Score."""

    def __init__(self, components: list[BaseScoreComponent] | None = None) -> None:
        self.components: list[BaseScoreComponent] = components or []

    def add_component(self, component: BaseScoreComponent) -> None:
        """Add a scoring component to the aggregator."""
        self.components.append(component)

    def calculate(self, context: AnalysisContext) -> AggregatedDealScore:
        """Calculate weighted aggregated Deal Score."""
        if not self.components:
            return AggregatedDealScore(
                total_score=50,
                raw_score=50.0,
                components={},
                summary="Brak aktywnych komponentów scoringowych.",
            )

        results: dict[str, ComponentScoreResult] = {}
        total_weight = 0.0
        weighted_sum = 0.0

        for comp in self.components:
            res = comp.calculate(context)
            # Clamp component score to [0, 100]
            clamped_score = max(0.0, min(100.0, float(res.score)))
            weight = max(0.0, float(res.weight))
            w_score = clamped_score * weight

            res.score = round(clamped_score, 1)
            res.weighted_score = round(w_score, 2)
            results[res.name] = res

            total_weight += weight
            weighted_sum += w_score

        if total_weight > 0:
            final_raw = weighted_sum / total_weight
        else:
            final_raw = 50.0

        final_score = max(0, min(100, round(final_raw)))

        if final_score >= 80:
            summary = "Wyjątkowa okazja cenowa i jakościowa!"
        elif final_score >= 65:
            summary = "Bardzo dobra oferta w stosunku do rynku."
        elif final_score >= 45:
            summary = "Przeciętna oferta rynkowa."
        else:
            summary = "Oferta poniżej średniego poziomu opłacalności."

        return AggregatedDealScore(
            total_score=final_score,
            raw_score=round(final_raw, 2),
            components=results,
            summary=summary,
        )
