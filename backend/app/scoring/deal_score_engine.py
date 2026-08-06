"""Deal Score Engine aggregating components to answer 'Czy warto kupić tę ofertę TERAZ?'"""

from typing import Any
from app.scoring.base_component import BaseScoringComponent
from app.scoring.components import (
    AvailabilityComponent,
    CompletenessComponent,
    MarketComponent,
    SeasonComponent,
    ValueScoreComponent,
)
from app.scoring.confidence_engine import ConfidenceEngine
from app.scoring.explainability import ExplainabilityLayer
from app.scoring.models import ComponentResult, DealScore, ValueScore
from app.scoring.value_engine import ValueEngine


class DealScoreEngine:
    """Component-based Deal Score Engine evaluating purchase attractiveness (0-100)."""

    def __init__(self, components: list[BaseScoringComponent] | None = None) -> None:
        self.components: list[BaseScoringComponent] = components or [
            ValueScoreComponent(),
            MarketComponent(),
            SeasonComponent(),
            CompletenessComponent(),
            AvailabilityComponent(),
        ]
        self.value_engine = ValueEngine()
        self.confidence_engine = ConfidenceEngine()

    def add_component(self, component: BaseScoringComponent) -> None:
        """Add a custom component to Deal Score Engine."""
        self.components.append(component)

    def calculate(
        self,
        offer: Any,
        context: dict[str, Any] | None = None,
        diagnostic: bool = False,
    ) -> DealScore:
        """Calculate primary DealScore, ConfidenceScore, and diagnostic details."""
        ctx = dict(context or {})

        # Compute ValueScore if not provided
        if "value_score" not in ctx:
            val_score_obj = self.value_engine.calculate(offer, ctx)
            ctx["value_score"] = val_score_obj
        else:
            val_score_obj = ctx["value_score"]

        # Compute ConfidenceScore
        confidence_obj = self.confidence_engine.calculate(offer, ctx)

        results: list[ComponentResult] = []
        total_weight = 0.0
        weighted_sum = 0.0

        for comp in self.components:
            res = comp.calculate(offer, ctx)
            results.append(res)
            total_weight += res.weight
            weighted_sum += res.weighted_score

        raw_score = (weighted_sum / total_weight) if total_weight > 0 else 50.0
        clamped_score = max(0.0, min(100.0, raw_score))
        final_score = int(round(clamped_score))

        explanations = ExplainabilityLayer.explain_deal_score(final_score, results, confidence_obj)
        summary = explanations[0] if explanations else "Ocena atrakcyjności zakupu."

        val_numeric = float(val_score_obj.total_score) if isinstance(val_score_obj, ValueScore) else float(val_score_obj or 50.0)

        diag_dict = {}
        if diagnostic:
            diag_dict = {
                "components": [c.model_dump() for c in results],
                "raw_score": round(clamped_score, 2),
                "total_weight": round(total_weight, 2),
                "confidence": confidence_obj.model_dump(),
            }

        return DealScore(
            total_score=final_score,
            raw_score=round(clamped_score, 2),
            summary=summary,
            value_score=val_numeric,
            confidence=confidence_obj,
            components=results,
            explanations=explanations,
            diagnostic_details=diag_dict,
        )
