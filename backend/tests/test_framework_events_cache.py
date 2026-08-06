"""Tests for EventBus, Cache layer, and EngineRegistry."""

import pytest
from app.analysis_framework import (
    AnalysisCacheManager,
    AnalysisContext,
    AnalysisEventBus,
    AnalysisPipeline,
    AnalysisStartedEvent,
    BaseAnalysisEngine,
    EngineFinishedEvent,
    EngineRegistry,
    InMemoryAnalysisCache,
)


class DummyEngine(BaseAnalysisEngine):
    name = "dummy"
    requires = []
    provides = ["result"]

    async def analyze(self, context: AnalysisContext):
        return "ok"


@pytest.mark.asyncio
async def test_event_bus_publishing():
    bus = AnalysisEventBus()
    received_events = []

    def handle_started(evt: AnalysisStartedEvent):
        received_events.append(evt)

    bus.subscribe(AnalysisStartedEvent, handle_started)

    ctx = AnalysisContext(event_bus=bus)
    pipeline = AnalysisPipeline()
    await pipeline.execute(ctx, engines=[DummyEngine()])

    assert len(received_events) == 1
    assert received_events[0].target_type == "offer"


def test_engine_registry():
    registry = EngineRegistry()
    eng = DummyEngine()

    registry.register(eng)
    assert registry.contains("dummy")
    assert registry.get("dummy") is eng

    with pytest.raises(Exception):
        registry.register(eng, overwrite=False)

    registry.register(eng, overwrite=True)
    assert len(registry.list_engines()) == 1


@pytest.mark.asyncio
async def test_cache_hit_and_miss():
    cache = InMemoryAnalysisCache()
    manager = AnalysisCacheManager(cache)

    ctx1 = AnalysisContext()
    pipeline = AnalysisPipeline()

    async def run_fn(c):
        return await pipeline.execute(c, engines=[DummyEngine()])

    # First call: Cache Miss
    res1 = await manager.execute_cached("key_1", ctx1, run_fn)
    assert res1.artifacts.get("result") == "ok"
    assert res1.metadata.cache_used is False

    # Second call: Cache Hit
    ctx2 = AnalysisContext()
    res2 = await manager.execute_cached("key_1", ctx2, run_fn)
    assert res2.artifacts.get("result") == "ok"
    assert res2.metadata.cache_used is True
