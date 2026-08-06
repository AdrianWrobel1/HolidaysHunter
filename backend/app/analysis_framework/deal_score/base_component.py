"""Base component interface for Deal Score calculations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.analysis_framework.context import AnalysisContext


@dataclass
class ComponentScoreResult:
    """Output from a single scoring component."""

    name: str
    score: float  # 0 to 100
    weight: float  # 0.0 to 1.0 (relative weight)
    weighted_score: float
    explanation: str | None = None
    metadata: dict[str, Any] | None = None


class BaseScoreComponent(ABC):
    """Interface that every Deal Score component must implement."""

    name: str
    weight: float = 1.0

    @abstractmethod
    def calculate(self, context: AnalysisContext) -> ComponentScoreResult:
        """Calculate score (0-100) for this component given context."""
