"""Completeness component for Deal Score Engine."""

from typing import Any
from app.scoring.base_component import BaseScoringComponent
from app.scoring.models import ComponentResult


class CompletenessComponent(BaseScoringComponent):
    """Evaluates offer data filling percentage."""

    name = "completeness"
    label = "Kompletność Danych Oferty"
    weight = 0.15

    REQUIRED_FIELDS: list[str] = [
        "title", "country", "region", "city", "hotel_name",
        "hotel_stars", "departure_date", "return_date",
        "departure_city", "meal_type", "transport_type",
        "price_per_person", "offer_url", "image_url"
    ]

    def calculate(self, offer: Any, context: dict[str, Any] | None = None) -> ComponentResult:
        if not offer:
            raw_score = 0.0
            explanation = "Brak danych oferty."
        else:
            present = sum(1 for f in self.REQUIRED_FIELDS if getattr(offer, f, None) is not None)
            raw_score = (present / len(self.REQUIRED_FIELDS)) * 100.0
            explanation = f"Wypełnienie pól oferty wynosi {raw_score:.0f}% ({present}/{len(self.REQUIRED_FIELDS)})."

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
