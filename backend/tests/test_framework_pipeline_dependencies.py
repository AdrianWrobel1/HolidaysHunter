"""Tests for AnalysisPipeline topological resolution, requires/provides, and exceptions."""

import pytest
from app.analysis_framework import (
    AnalysisContext,
    AnalysisPipeline,
    BaseAnalysisEngine,
    CircularDependencyException,
    MissingDependencyException,
)


class EngineA(BaseAnalysisEngine):
    name = "engine_a"
    requires = []
    provides = ["artifact_a"]

    async def analyze(self, context: AnalysisContext):
        return "data_a"


class EngineB(BaseAnalysisEngine):
    name = "engine_b"
    requires = ["artifact_a"]
    provides = ["artifact_b"]

    async def analyze(self, context: AnalysisContext):
        data_a = context.artifacts["artifact_a"]
        return f"{data_a}_and_b"


class EngineC(BaseAnalysisEngine):
    name = "engine_c"
    requires = ["artifact_b"]
    provides = ["artifact_c"]

    async def analyze(self, context: AnalysisContext):
        data_b = context.artifacts["artifact_b"]
        return f"{data_b}_and_c"


class Circular1(BaseAnalysisEngine):
    name = "circ_1"
    requires = ["key_2"]
    provides = ["key_1"]

    async def analyze(self, context: AnalysisContext):
        return 1


class Circular2(BaseAnalysisEngine):
    name = "circ_2"
    requires = ["key_1"]
    provides = ["key_2"]

    async def analyze(self, context: AnalysisContext):
        return 2


@pytest.mark.asyncio
async def test_pipeline_topological_resolution_and_execution():
    pipeline = AnalysisPipeline()
    # Pass engines out of order: C, B, A
    engines = [EngineC(), EngineB(), EngineA()]
    context = AnalysisContext()

    resolved_context = await pipeline.execute(context, engines=engines)

    assert resolved_context.artifacts.get("artifact_a") == "data_a"
    assert resolved_context.artifacts.get("artifact_b") == "data_a_and_b"
    assert resolved_context.artifacts.get("artifact_c") == "data_a_and_b_and_c"

    assert resolved_context.metadata.engines_executed == ["engine_a", "engine_b", "engine_c"]
    assert len(resolved_context.metadata.failed_engines) == 0


@pytest.mark.asyncio
async def test_pipeline_missing_dependency_raises():
    pipeline = AnalysisPipeline()
    # Only B provided, but B requires artifact_a
    engines = [EngineB()]
    context = AnalysisContext()

    with pytest.raises(MissingDependencyException) as exc_info:
        await pipeline.execute(context, engines=engines)

    assert "requires missing artifacts ['artifact_a']" in str(exc_info.value)


@pytest.mark.asyncio
async def test_pipeline_circular_dependency_raises():
    pipeline = AnalysisPipeline()
    engines = [Circular1(), Circular2()]
    context = AnalysisContext()

    with pytest.raises(CircularDependencyException):
        await pipeline.execute(context, engines=engines)
