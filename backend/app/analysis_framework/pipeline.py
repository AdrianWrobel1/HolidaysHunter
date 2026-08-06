"""Analysis Pipeline with topological dependency resolution and event publishing."""

from collections import defaultdict, deque
import logging
import time
from typing import Any

from app.analysis_framework.base_engine import BaseAnalysisEngine
from app.analysis_framework.context import AnalysisContext
from app.analysis_framework.events import (
    AnalysisFinishedEvent,
    AnalysisStartedEvent,
    EngineFailedEvent,
    EngineFinishedEvent,
    EngineStartedEvent,
)
from app.analysis_framework.exceptions import (
    CircularDependencyException,
    EngineExecutionException,
    MissingDependencyException,
)
from app.analysis_framework.metadata import EngineExecutionResult
from app.analysis_framework.registry import EngineRegistry

logger = logging.getLogger(__name__)


class AnalysisPipeline:
    """Orchestrates execution of registered engines in topological dependency order."""

    def __init__(self, registry: EngineRegistry | None = None) -> None:
        self.registry = registry

    def resolve_execution_order(
        self,
        engines: list[BaseAnalysisEngine],
        initial_provided: set[str],
    ) -> list[BaseAnalysisEngine]:
        """Compute topological order for engines based on requires and provides.

        Raises:
            MissingDependencyException: If an engine requires an artifact not provided.
            CircularDependencyException: If circular dependencies exist between engines.
        """
        provided_set = set(initial_provided)
        for eng in engines:
            provided_set.update(eng.provides)

        # 1. Verify all required keys are satisfies somewhere
        for eng in engines:
            missing = [req for req in eng.requires if req not in provided_set]
            if missing:
                raise MissingDependencyException(
                    f"Engine '{eng.name}' requires missing artifacts {missing} which are not provided by any engine or initial context."
                )

        # 2. Build dependency graph between engines
        # Engine A depends on Engine B if B provides a key required by A (and key not in initial_provided)
        engine_by_name = {eng.name: eng for eng in engines}
        key_provider: dict[str, str] = {}
        for eng in engines:
            for prov in eng.provides:
                key_provider[prov] = eng.name

        in_degree: dict[str, int] = {eng.name: 0 for eng in engines}
        adj_list: dict[str, list[str]] = defaultdict(list)

        for eng in engines:
            for req in eng.requires:
                if req in initial_provided:
                    continue
                provider_engine = key_provider.get(req)
                if provider_engine and provider_engine != eng.name:
                    adj_list[provider_engine].append(eng.name)
                    in_degree[eng.name] += 1

        # 3. Kahn's Algorithm for Topological Sort
        queue = deque([name for name, deg in in_degree.items() if deg == 0])
        ordered_names: list[str] = []

        while queue:
            curr = queue.popleft()
            ordered_names.append(curr)
            for neighbor in adj_list[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(ordered_names) != len(engines):
            unprocessed = [name for name, deg in in_degree.items() if deg > 0]
            raise CircularDependencyException(
                f"Circular dependency detected involving engines: {unprocessed}"
            )

        return [engine_by_name[name] for name in ordered_names]

    async def execute(
        self,
        context: AnalysisContext,
        engines: list[BaseAnalysisEngine] | None = None,
    ) -> AnalysisContext:
        """Execute pipeline for given context."""
        if engines is None:
            if not self.registry:
                raise ValueError("No engines provided and no registry configured for pipeline.")
            engines = self.registry.list_engines()

        initial_keys = set(context.artifacts.list_keys())
        ordered_engines = self.resolve_execution_order(engines, initial_keys)

        context.metadata.target_type = context.target_type
        if context.provider:
            prov_str = context.provider.value if hasattr(context.provider, "value") else str(context.provider)
            context.metadata.provider = prov_str

        await context.event_bus.publish(
            AnalysisStartedEvent(
                analysis_id=context.metadata.analysis_id,
                target_type=context.target_type,
            )
        )

        for engine in ordered_engines:
            # Check requirements in current context
            missing_at_runtime = [
                req for req in engine.requires if not context.artifacts.has(req)
            ]
            if missing_at_runtime:
                err_msg = f"Engine '{engine.name}' missing runtime artifacts: {missing_at_runtime}"
                context.metadata.failed_engines.append(engine.name)
                await context.event_bus.publish(
                    EngineFailedEvent(
                        analysis_id=context.metadata.analysis_id,
                        engine_name=engine.name,
                        error_message=err_msg,
                    )
                )
                raise MissingDependencyException(err_msg)

            await context.event_bus.publish(
                EngineStartedEvent(
                    analysis_id=context.metadata.analysis_id,
                    engine_name=engine.name,
                )
            )

            start_t = time.perf_counter()
            exec_result = EngineExecutionResult(
                engine_name=engine.name,
                success=False,
                duration_ms=0.0,
                provided_keys=engine.provides.copy(),
            )

            try:
                result = await engine.analyze(context)
                duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
                exec_result.duration_ms = duration_ms
                exec_result.success = True

                # Save primary artifact if engine returned a value and provides a key
                if result is not None:
                    if engine.provides:
                        primary_key = engine.provides[0]
                        if isinstance(result, dict) and len(engine.provides) > 1 and all(k in result for k in engine.provides):
                            for k, v in result.items():
                                context.artifacts.set(k, v)
                        else:
                            context.artifacts.set(primary_key, result)

                context.metadata.engines_executed.append(engine.name)
                context.metadata.engine_results.append(exec_result)

                await context.event_bus.publish(
                    EngineFinishedEvent(
                        analysis_id=context.metadata.analysis_id,
                        engine_name=engine.name,
                        duration_ms=duration_ms,
                        provided_keys=engine.provides,
                    )
                )
            except Exception as exc:
                duration_ms = round((time.perf_counter() - start_t) * 1000, 2)
                exec_result.duration_ms = duration_ms
                exec_result.errors.append(str(exc))
                context.metadata.failed_engines.append(engine.name)
                context.metadata.engine_results.append(exec_result)

                await context.event_bus.publish(
                    EngineFailedEvent(
                        analysis_id=context.metadata.analysis_id,
                        engine_name=engine.name,
                        error_message=str(exc),
                    )
                )
                logger.exception("Engine '%s' execution failed: %s", engine.name, exc)
                raise EngineExecutionException(
                    f"Engine '{engine.name}' failed: {exc}"
                ) from exc

        context.metadata.mark_finished(cache_used=False)
        await context.event_bus.publish(
            AnalysisFinishedEvent(
                analysis_id=context.metadata.analysis_id,
                duration_ms=context.metadata.duration_ms or 0.0,
                cache_used=False,
                success=True,
            )
        )

        return context
