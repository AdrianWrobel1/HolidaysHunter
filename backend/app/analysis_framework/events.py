"""Event Bus and Analysis Lifecycle Events."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine


@dataclass
class BaseAnalysisEvent:
    """Base lifecycle event emitted during analysis execution."""

    analysis_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class AnalysisStartedEvent(BaseAnalysisEvent):
    target_type: str = "offer"


@dataclass
class AnalysisFinishedEvent(BaseAnalysisEvent):
    duration_ms: float = 0.0
    cache_used: bool = False
    success: bool = True


@dataclass
class EngineStartedEvent(BaseAnalysisEvent):
    engine_name: str = ""


@dataclass
class EngineFinishedEvent(BaseAnalysisEvent):
    engine_name: str = ""
    duration_ms: float = 0.0
    provided_keys: list[str] = field(default_factory=list)


@dataclass
class EngineFailedEvent(BaseAnalysisEvent):
    engine_name: str = ""
    error_message: str = ""


@dataclass
class CacheHitEvent(BaseAnalysisEvent):
    key: str = ""


@dataclass
class CacheMissEvent(BaseAnalysisEvent):
    key: str = ""


EventListener = Callable[[BaseAnalysisEvent], Coroutine[Any, Any, None] | None]


class AnalysisEventBus:
    """Asynchronous Event Bus for broadcasting framework lifecycle events."""

    def __init__(self) -> None:
        self._listeners: dict[type[BaseAnalysisEvent], list[EventListener]] = {}

    def subscribe(
        self,
        event_type: type[BaseAnalysisEvent],
        listener: EventListener,
    ) -> None:
        """Register an event listener for a specific event type."""
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    async def publish(self, event: BaseAnalysisEvent) -> None:
        """Publish an event to all subscribed listeners."""
        event_type = type(event)
        listeners = self._listeners.get(event_type, [])
        for listener in listeners:
            try:
                res = listener(event)
                if asyncio.iscoroutine(res):
                    await res
            except Exception:
                # Event listeners must never crash the pipeline
                pass
