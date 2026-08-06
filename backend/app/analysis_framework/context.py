"""Central Analysis Context holding state, artifacts, session, and metadata."""

from dataclasses import dataclass, field
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis_framework.artifacts import ArtifactStore
from app.analysis_framework.events import AnalysisEventBus
from app.analysis_framework.metadata import AnalysisMetadata
from app.models.enums import Provider


@dataclass
class AnalysisContext:
    """Central context passed through the analysis pipeline."""

    target_type: str = "offer"
    analyzed_object: Any = None
    provider: Provider | str | None = None
    raw_payload: dict[str, Any] | None = None
    candidate_objects: list[Any] = field(default_factory=list)
    session: AsyncSession | None = None
    config: dict[str, Any] = field(default_factory=dict)
    artifacts: ArtifactStore = field(default_factory=ArtifactStore)
    metadata: AnalysisMetadata = field(default_factory=AnalysisMetadata)
    event_bus: AnalysisEventBus = field(default_factory=AnalysisEventBus)

    @property
    def analysis_data(self) -> ArtifactStore:
        """Alias for artifacts to maintain backward compatibility."""
        return self.artifacts
