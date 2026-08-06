"""Transport Value component for Value Engine."""

from typing import Any
from app.models.enums import TransportType
from app.scoring.base_component import BaseScoringComponent
from app.scoring.models import ComponentResult


class TransportValueComponent(BaseScoringComponent):
    """Evaluates transport mode value baseline (Flight vs Self Transport vs Bus)."""

    name = "transport_value"
    label = "Komfort i Wartość Transportu"
    weight = 0.10

    def calculate(self, offer: Any, context: dict[str, Any] | None = None) -> ComponentResult:
        ttype = getattr(offer, "transport_type", TransportType.FLIGHT)
        ttype_str = ttype.value if hasattr(ttype, "value") else str(ttype).lower()

        if ttype_str == TransportType.FLIGHT.value:
            raw_score = 90.0
            dep_city = getattr(offer, "departure_city", None)
            explanation = f"Przelot samolotem z {dep_city if dep_city else 'lotniska'}."
        elif ttype_str in (TransportType.SELF_TRANSPORT.value, "own"):
            raw_score = 60.0
            explanation = "Dojazd własny (brak kosztów przelotu w cenie pakietu)."
        elif ttype_str == TransportType.BUS.value:
            raw_score = 55.0
            explanation = "Dojazd autokarem."
        elif ttype_str == TransportType.TRAIN.value:
            raw_score = 70.0
            explanation = "Dojazd pociągiem."
        elif ttype_str == TransportType.CRUISE.value:
            raw_score = 95.0
            explanation = "Rejs wycieczkowy."
        else:
            raw_score = 50.0
            explanation = "Nieokreślony środek transportu."

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
