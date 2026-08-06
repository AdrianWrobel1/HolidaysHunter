"""Availability component for Deal Score Engine."""

from typing import Any
from app.scoring.base_component import BaseScoringComponent
from app.scoring.models import ComponentResult


class AvailabilityComponent(BaseScoringComponent):
    """Evaluates availability and urgency status of the offer."""

    name = "availability"
    label = "Dostępność i Status Rezerwacji"
    weight = 0.10

    def calculate(self, offer: Any, context: dict[str, Any] | None = None) -> ComponentResult:
        is_avail = getattr(offer, "is_available", True)
        if is_avail is None:
            is_avail = True

        if is_avail:
            raw_score = 90.0
            explanation = "Oferta jest aktualnie dostępna do rezerwacji."
        else:
            raw_score = 20.0
            explanation = "Oferta nie jest już dostępna u organizatora."

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
