"""Core models for framework reports and results."""

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field


class BaseAnalysisReport(BaseModel):
    """Base Pydantic schema for all analysis reports produced by framework."""

    analysis_id: str
    target_type: str
    started_at: datetime
    finished_at: datetime | None = None
    duration_ms: float | None = None
    framework_version: str = "1.0.0"
    cache_used: bool = False
    provider: str | None = None
    engines_executed: list[str] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
