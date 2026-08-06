"""Cache layer interface and default implementations for Analysis Framework."""

from abc import ABC, abstractmethod
from typing import Any

from app.analysis_framework.context import AnalysisContext
from app.analysis_framework.events import CacheHitEvent, CacheMissEvent


class BaseAnalysisCache(ABC):
    """Abstract interface for caching analysis results."""

    @abstractmethod
    async def get(self, cache_key: str) -> dict[str, Any] | None:
        """Retrieve cached artifacts dict or None on miss."""

    @abstractmethod
    async def set(self, cache_key: str, data: dict[str, Any], ttl_seconds: int = 3600) -> None:
        """Store artifacts dict in cache."""

    @abstractmethod
    async def invalidate(self, cache_key: str) -> None:
        """Invalidate a specific cache key."""


class InMemoryAnalysisCache(BaseAnalysisCache):
    """Simple in-memory dictionary cache implementation."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}

    async def get(self, cache_key: str) -> dict[str, Any] | None:
        return self._store.get(cache_key)

    async def set(self, cache_key: str, data: dict[str, Any], ttl_seconds: int = 3600) -> None:
        self._store[cache_key] = data

    async def invalidate(self, cache_key: str) -> None:
        self._store.pop(cache_key, None)


class AnalysisCacheManager:
    """Manager wrapping pipeline execution with cache lookup and storage."""

    def __init__(self, cache: BaseAnalysisCache) -> None:
        self.cache = cache

    async def execute_cached(
        self,
        cache_key: str,
        context: AnalysisContext,
        execute_pipeline_fn: Any,
        ttl_seconds: int = 3600,
    ) -> AnalysisContext:
        """Attempt cache lookup before executing pipeline."""
        cached_data = await self.cache.get(cache_key)
        if cached_data is not None:
            for k, v in cached_data.items():
                context.artifacts.set(k, v)
            context.metadata.mark_finished(cache_used=True)
            await context.event_bus.publish(
                CacheHitEvent(analysis_id=context.metadata.analysis_id, key=cache_key)
            )
            return context

        await context.event_bus.publish(
            CacheMissEvent(analysis_id=context.metadata.analysis_id, key=cache_key)
        )

        executed_context = await execute_pipeline_fn(context)
        await self.cache.set(
            cache_key,
            executed_context.artifacts.to_dict(),
            ttl_seconds=ttl_seconds,
        )
        return executed_context
