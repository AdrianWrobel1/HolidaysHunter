"""Engine Registry for discovering and managing analysis engines."""

import logging

from app.analysis_framework.base_engine import BaseAnalysisEngine
from app.analysis_framework.exceptions import (
    DuplicateEngineException,
    EngineNotFoundException,
)

logger = logging.getLogger(__name__)


class EngineRegistry:
    """Central registry of analysis engine instances."""

    def __init__(self) -> None:
        self._engines: dict[str, BaseAnalysisEngine] = {}

    def register(self, engine: BaseAnalysisEngine, overwrite: bool = False) -> None:
        """Register an analysis engine instance."""
        if not engine.name:
            raise ValueError("Engine name cannot be empty.")
        if engine.name in self._engines and not overwrite:
            raise DuplicateEngineException(
                f"Engine '{engine.name}' is already registered."
            )
        self._engines[engine.name] = engine
        logger.debug("Registered analysis engine '%s'", engine.name)

    def get(self, name: str) -> BaseAnalysisEngine:
        """Get registered engine by name."""
        if name not in self._engines:
            raise EngineNotFoundException(f"Engine '{name}' not found in registry.")
        return self._engines[name]

    def contains(self, name: str) -> bool:
        """Check if engine is registered."""
        return name in self._engines

    def list_engines(self) -> list[BaseAnalysisEngine]:
        """Return list of all registered engines."""
        return list(self._engines.values())

    def clear(self) -> None:
        """Remove all registered engines."""
        self._engines.clear()


# Global default engine registry instance
global_engine_registry = EngineRegistry()
