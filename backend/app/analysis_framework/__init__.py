"""Universal Analysis Framework."""

from app.analysis_framework.artifacts import ArtifactStore
from app.analysis_framework.base_engine import BaseAnalysisEngine
from app.analysis_framework.cache import (
    AnalysisCacheManager,
    BaseAnalysisCache,
    InMemoryAnalysisCache,
)
from app.analysis_framework.context import AnalysisContext
from app.analysis_framework.events import (
    AnalysisEventBus,
    AnalysisFinishedEvent,
    AnalysisStartedEvent,
    BaseAnalysisEvent,
    CacheHitEvent,
    CacheMissEvent,
    EngineFailedEvent,
    EngineFinishedEvent,
    EngineStartedEvent,
)
from app.analysis_framework.exceptions import (
    CircularDependencyException,
    DuplicateEngineException,
    EngineExecutionException,
    EngineNotFoundException,
    FrameworkException,
    MissingDependencyException,
)
from app.analysis_framework.metadata import AnalysisMetadata, EngineExecutionResult
from app.analysis_framework.pipeline import AnalysisPipeline
from app.analysis_framework.registry import EngineRegistry, global_engine_registry

__all__ = [
    "AnalysisContext",
    "ArtifactStore",
    "BaseAnalysisEngine",
    "EngineRegistry",
    "global_engine_registry",
    "AnalysisPipeline",
    "AnalysisEventBus",
    "BaseAnalysisEvent",
    "AnalysisStartedEvent",
    "AnalysisFinishedEvent",
    "EngineStartedEvent",
    "EngineFinishedEvent",
    "EngineFailedEvent",
    "CacheHitEvent",
    "CacheMissEvent",
    "AnalysisMetadata",
    "EngineExecutionResult",
    "BaseAnalysisCache",
    "InMemoryAnalysisCache",
    "AnalysisCacheManager",
    "FrameworkException",
    "MissingDependencyException",
    "CircularDependencyException",
    "EngineExecutionException",
    "DuplicateEngineException",
    "EngineNotFoundException",
]
