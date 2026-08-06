"""Base Analysis Engine interface with explicit dependencies (requires & provides)."""

from abc import ABC, abstractmethod
from typing import Any

from app.analysis_framework.context import AnalysisContext


class BaseAnalysisEngine(ABC):
    """Abstract interface that every Analysis Engine must implement.

    Each engine declares:
    - name: Unique identifier for the engine
    - requires: Artifact keys that MUST exist in context.artifacts before execution
    - provides: Artifact keys that this engine produces and stores into context.artifacts
    """

    name: str
    requires: list[str] = []
    provides: list[str] = []

    @abstractmethod
    async def analyze(self, context: AnalysisContext) -> Any:
        """Execute the engine logic using context.

        Returns the main artifact produced by this engine, which the pipeline
        will automatically assign to context.artifacts[self.provides[0]].
        If provides contains multiple keys, the engine should manually populate
        context.artifacts for extra keys or return a dict mapping keys to artifacts.
        """
