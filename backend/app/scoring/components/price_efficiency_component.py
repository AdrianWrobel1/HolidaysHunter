"""Price Efficiency component for Value Engine."""

from typing import Any
from app.scoring.base_component import BaseScoringComponent
from app.scoring.models import ComponentResult


class PriceEfficiencyComponent(BaseScoringComponent):
    """Evaluates per-person per-day price relative to market baseline."""

    name = "price_efficiency"
    label = "Efektywność Cenowa za Dzień"
    weight = 0.30

    def calculate(self, offer: Any, context: dict[str, Any] | None = None) -> ComponentResult:
        price_pp = float(getattr(offer, "price_per_person", 0) or 0)
        nights = int(getattr(offer, "duration_nights", 7) or 7)
        if nights <= 0:
            nights = 7

        person_daily = price_pp / nights if price_pp > 0 else 0

        stats = (context or {}).get("statistics", {})
        mean_price_pp = stats.get("mean_price_per_person", 3500.0) or 3500.0
        market_daily = mean_price_pp / 7.0

        if person_daily <= 0 or market_daily <= 0:
            raw_score = 50.0
            explanation = f"Stawka za osobę: {person_daily:.0f} PLN/dzień."
        else:
            diff_pct = ((person_daily - market_daily) / market_daily) * 100.0
            # If 30% lower than market daily -> 100 pts, equal -> 50 pts, 30% higher -> 0 pts
            raw_score = max(0.0, min(100.0, 50.0 - (diff_pct * 1.67)))
            explanation = f"Dniowa stawka: {person_daily:.0f} PLN/os/dzień (średnia rynkowa: {market_daily:.0f} PLN)."

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
