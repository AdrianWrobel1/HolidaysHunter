"""Meal Value component for Value Engine."""

from typing import Any
from app.scoring.base_component import BaseScoringComponent
from app.scoring.models import ComponentResult


class MealValueComponent(BaseScoringComponent):
    """Evaluates the value tier of the meal plan included in the offer."""

    name = "meal_value"
    label = "Wartość Wyżywienia"
    weight = 0.15

    MEAL_SCORES: dict[str, float] = {
        "all_inclusive": 100.0,
        "full_board": 80.0,
        "half_board": 65.0,
        "bed_and_breakfast": 50.0,
        "self_catering": 35.0,
    }

    def calculate(self, offer: Any, context: dict[str, Any] | None = None) -> ComponentResult:
        raw_meal = str(getattr(offer, "meal_type", "") or "").strip().lower()

        raw_score = 50.0
        for key, sc in self.MEAL_SCORES.items():
            if key in raw_meal:
                raw_score = sc
                break

        weighted_score = raw_score * self.weight
        impact = (raw_score - 50.0) * self.weight

        meal_name = raw_meal.replace("_", " ").title() if raw_meal else "Brak danych"
        explanation = f"Opcja wyżywienia: {meal_name}."

        return ComponentResult(
            name=self.name,
            label=self.label,
            score=round(raw_score, 1),
            weight=self.weight,
            weighted_score=round(weighted_score, 2),
            impact=round(impact, 2),
            explanation=explanation,
        )
