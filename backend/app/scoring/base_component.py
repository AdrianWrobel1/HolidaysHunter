"""Base abstract scoring component interface."""

from abc import ABC, abstractmethod
from typing import Any

from app.scoring.models import ComponentResult


class BaseScoringComponent(ABC):
    """Abstract base class for all single-responsibility scoring components."""

    name: str = "base_component"
    label: str = "Base Component"
    weight: float = 0.10

    @abstractmethod
    def calculate(self, offer: Any, context: dict[str, Any] | None = None) -> ComponentResult:
        """Calculate score, weight, net impact, and explanation for an offer."""
        pass
