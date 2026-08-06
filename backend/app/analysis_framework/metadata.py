"""Analysis metadata and engine execution diagnostics."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


@dataclass
class EngineExecutionResult:
    """Execution telemetry for a single engine run."""

    engine_name: str
    success: bool
    duration_ms: float
    provided_keys: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class AnalysisMetadata:
    """Comprehensive analysis execution metadata."""

    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    duration_ms: float | None = None
    framework_version: str = "1.0.0"
    target_type: str = "offer"
    provider: str | None = None
    cache_used: bool = False
    engines_executed: list[str] = field(default_factory=list)
    failed_engines: list[str] = field(default_factory=list)
    engine_results: list[EngineExecutionResult] = field(default_factory=list)

    def mark_finished(self, cache_used: bool = False) -> None:
        self.finished_at = datetime.now(timezone.utc)
        self.duration_ms = round(
            (self.finished_at - self.started_at).total_seconds() * 1000, 2
        )
        self.cache_used = cache_used
