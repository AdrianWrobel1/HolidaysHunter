"""Modular Deal Score Framework."""

from app.analysis_framework.deal_score.aggregator import (
    AggregatedDealScore,
    DealScoreAggregator,
)
from app.analysis_framework.deal_score.base_component import (
    BaseScoreComponent,
    ComponentScoreResult,
)
from app.analysis_framework.deal_score.components.completeness_score import (
    CompletenessScoreComponent,
)
from app.analysis_framework.deal_score.components.market_score import (
    MarketScoreComponent,
)
from app.analysis_framework.deal_score.components.price_score import (
    PriceScoreComponent,
)
from app.analysis_framework.deal_score.components.quality_score import (
    QualityScoreComponent,
)
from app.analysis_framework.deal_score.components.season_score import (
    SeasonScoreComponent,
)
from app.analysis_framework.deal_score.components.similarity_score import (
    SimilarityScoreComponent,
)

__all__ = [
    "BaseScoreComponent",
    "ComponentScoreResult",
    "DealScoreAggregator",
    "AggregatedDealScore",
    "PriceScoreComponent",
    "SimilarityScoreComponent",
    "MarketScoreComponent",
    "QualityScoreComponent",
    "SeasonScoreComponent",
    "CompletenessScoreComponent",
]
