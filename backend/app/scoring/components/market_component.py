"""Market Position component for Deal Score Engine."""

from typing import Any
from app.scoring.base_component import BaseScoringComponent
from app.scoring.models import ComponentResult


class MarketComponent(BaseScoringComponent):
    """Evaluates offer price percentile rank relative to market candidates."""

    name = "market_position"
    label = "Pozycja Rynkowa (Percentyl Ceny)"
    weight = 0.25

    def calculate(self, offer: Any, context: dict[str, Any] | None = None) -> ComponentResult:
        market_pos = (context or {}).get("market_position", {})
        if isinstance(market_pos, dict) and "cheaper_than_pct" in market_pos:
            cheaper_pct = float(market_pos.get("cheaper_than_pct", 50.0))
        else:
            cheaper_pct = 50.0

        raw_score = max(0.0, min(100.0, cheaper_pct))
        weighted_score = raw_score * self.weight
        impact = (raw_score - 50.0) * self.weight

        explanation = f"Oferta jest tańsza niż {cheaper_pct:.0f}% analizowanych ofert rynkowych."

        return ComponentResult(
            name=self.name,
            label=self.label,
            score=round(raw_score, 1),
            weight=self.weight,
            weighted_score=round(weighted_score, 2),
            impact=round(impact, 2),
            explanation=explanation,
        )
