"""Offer Analyzer orchestrator service built on top of Analysis Framework."""

import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis_framework import (
    AnalysisCacheManager,
    AnalysisContext,
    AnalysisPipeline,
    EngineRegistry,
    InMemoryAnalysisCache,
)
from app.offer_analyzer.engines import (
    DealScoreEngine,
    MarketPositionEngine,
    OfferQualityEngine,
    PriceEfficiencyEngine,
    PriceStatisticsEngine,
    RecommendationEngine,
    SimilarOffersEngine,
    VisualizationEngine,
)
from app.offer_analyzer.models import (
    BoxPlotData,
    DealScoreBreakdown,
    DealScoreComponentSchema,
    HistogramBin,
    MarketPosition,
    OfferAnalysisReport,
    OfferQuality,
    PriceAnalysis,
    PriceEfficiency,
    Recommendation,
    SimilarOfferItem,
    SimilarityAnalysis,
    TargetOfferSummary,
    VisualizationData,
)
from app.offer_analyzer.parser import parse_offer_from_url
from app.providers.schemas import NormalizedOffer

logger = logging.getLogger(__name__)

# Global cache instance for Offer Analyzer
_offer_analyzer_cache = InMemoryAnalysisCache()
_cache_manager = AnalysisCacheManager(_offer_analyzer_cache)


def _build_offer_analyzer_registry() -> EngineRegistry:
    """Build and populate engine registry for Offer Analyzer."""
    reg = EngineRegistry()
    reg.register(SimilarOffersEngine())
    reg.register(OfferQualityEngine())
    reg.register(PriceStatisticsEngine())
    reg.register(MarketPositionEngine())
    reg.register(PriceEfficiencyEngine())
    reg.register(DealScoreEngine())
    reg.register(RecommendationEngine())
    reg.register(VisualizationEngine())
    return reg


async def analyze_offer_url(
    url: str,
    session: AsyncSession | None = None,
    candidate_offers: list[Any] | None = None,
) -> OfferAnalysisReport:
    """Analyze travel offer from URL using Universal Analysis Framework.

    Pipeline execution steps:
    1. Parse URL & detect provider via existing provider layer -> NormalizedOffer
    2. Build AnalysisContext
    3. Run AnalysisPipeline with registered engines
    4. Format and return OfferAnalysisReport
    """
    logger.info("OfferAnalyzer: START analysis for URL '%s'", url)

    # 1. Parse offer via provider layer
    normalized: NormalizedOffer = await parse_offer_from_url(url)

    # 2. Build AnalysisContext
    context = AnalysisContext(
        target_type="offer",
        analyzed_object=normalized,
        provider=normalized.provider,
        raw_payload=None,
        candidate_objects=candidate_offers or [],
        session=session,
    )

    # 3. Execute AnalysisPipeline
    registry = _build_offer_analyzer_registry()
    pipeline = AnalysisPipeline(registry=registry)

    cache_key = f"offer-analysis-{url}"

    async def _run_pipeline(ctx: AnalysisContext) -> AnalysisContext:
        return await pipeline.execute(ctx)

    result_context = await _cache_manager.execute_cached(
        cache_key=cache_key,
        context=context,
        execute_pipeline_fn=_run_pipeline,
        ttl_seconds=300,
    )

    artifacts = result_context.artifacts
    meta = result_context.metadata

    # 4. Extract artifacts & map to response model
    sim_data = artifacts.get("similarity", {})
    stats_data = artifacts.get("statistics", {})
    mkt_data = artifacts.get("market_position", {})
    eff_data = artifacts.get("price_efficiency", {})
    qual_data = artifacts.get("offer_quality", {})
    score_data = artifacts.get("deal_score", {})
    rec_data = artifacts.get("recommendation", {})
    vis_data = artifacts.get("visualization", {})

    target_summary = TargetOfferSummary(
        external_id=normalized.external_id,
        provider=normalized.provider.value if hasattr(normalized.provider, "value") else str(normalized.provider),
        title=normalized.title,
        country=normalized.country,
        region=normalized.region,
        city=normalized.city,
        hotel_name=normalized.hotel_name,
        hotel_stars=normalized.hotel_stars,
        hotel_rating=normalized.hotel_rating,
        departure_date=normalized.departure_date,
        return_date=normalized.return_date,
        duration_nights=normalized.duration_nights,
        departure_city=normalized.departure_city,
        adults=normalized.adults,
        children=normalized.children,
        meal_type=normalized.meal_type.value if hasattr(normalized.meal_type, "value") else str(normalized.meal_type),
        transport_type=normalized.transport_type.value if hasattr(normalized.transport_type, "value") else str(normalized.transport_type),
        price_total=normalized.price_total,
        price_per_person=normalized.price_per_person,
        currency=normalized.currency,
        offer_url=normalized.offer_url,
        image_url=normalized.image_url,
    )

    top_matches = [
        SimilarOfferItem(
            id=item.get("id"),
            external_id=item["external_id"],
            provider=item["provider"],
            title=item["title"],
            hotel_name=item["hotel_name"],
            country=item["country"],
            region=item.get("region"),
            hotel_stars=item.get("hotel_stars"),
            departure_date=item["departure_date"],
            duration_nights=item["duration_nights"],
            meal_type=item["meal_type"],
            departure_city=item["departure_city"],
            price_per_person=item["price_per_person"],
            similarity_score=item["similarity_score"],
            explanations=item["explanations"],
        )
        for item in sim_data.get("top_matches", [])
    ]

    similarity_analysis = SimilarityAnalysis(
        candidates_count=sim_data.get("candidates_count", 0),
        top_matches=top_matches,
    )

    price_analysis = PriceAnalysis(
        min_price=stats_data.get("min_price", 0.0),
        max_price=stats_data.get("max_price", 0.0),
        mean_price=stats_data.get("mean_price", 0.0),
        median_price=stats_data.get("median_price", 0.0),
        std_dev=stats_data.get("std_dev", 0.0),
        percentile_25=stats_data.get("percentile_25", 0.0),
        percentile_75=stats_data.get("percentile_75", 0.0),
        target_price=stats_data.get("target_price", 0.0),
        price_per_day=stats_data.get("price_per_day", 0.0),
        price_per_person_per_day=stats_data.get("price_per_person_per_day", 0.0),
        price_diff_amount=stats_data.get("price_diff_amount", 0.0),
        price_diff_pct=stats_data.get("price_diff_pct", 0.0),
        position_summary=stats_data.get("position_summary", ""),
    )

    market_pos = MarketPosition(
        cheaper_than_pct=mkt_data.get("cheaper_than_pct", 50.0),
        more_expensive_than_pct=mkt_data.get("more_expensive_than_pct", 50.0),
        price_percentile=mkt_data.get("price_percentile", 50.0),
        rank_position=mkt_data.get("rank_position", 1),
        total_candidates=mkt_data.get("total_candidates", 1),
        rank_summary=mkt_data.get("rank_summary", ""),
    )

    price_eff = PriceEfficiency(
        daily_rate=eff_data.get("daily_rate", 0.0),
        person_daily_rate=eff_data.get("person_daily_rate", 0.0),
        market_avg_person_daily_rate=eff_data.get("market_avg_person_daily_rate", 0.0),
        efficiency_score=eff_data.get("efficiency_score", 50.0),
        summary=eff_data.get("summary", ""),
    )

    offer_qual = OfferQuality(
        quality_score=qual_data.get("quality_score", 50.0),
        completeness_pct=qual_data.get("completeness_pct", 100.0),
        highlights=qual_data.get("highlights", []),
    )

    components_schema = [
        DealScoreComponentSchema(
            name=comp["name"],
            score=comp["score"],
            weight=comp["weight"],
            weighted_score=comp["weighted_score"],
            impact=comp.get("impact", 0.0),
            explanation=comp.get("explanation"),
        )
        for comp in score_data.get("components", [])
    ]

    deal_score = DealScoreBreakdown(
        total_score=score_data.get("total_score", 50),
        raw_score=score_data.get("raw_score", 50.0),
        summary=score_data.get("summary", ""),
        value_score=score_data.get("value_score", 50.0),
        confidence=score_data.get("confidence", {}),
        components=components_schema,
        explanations=score_data.get("explanations", []),
    )

    recommendation = Recommendation(
        verdict_badge=rec_data.get("verdict_badge", "AVERAGE OFFER"),
        verdict_color=rec_data.get("verdict_color", "amber"),
        title=rec_data.get("title", "Standardowa oferta"),
        takeaways=rec_data.get("takeaways", []),
    )

    hist_bins = [
        HistogramBin(
            bin_label=b["bin_label"],
            bin_min=b["bin_min"],
            bin_max=b["bin_max"],
            count=b["count"],
            is_target_bin=b["is_target_bin"],
        )
        for b in vis_data.get("histogram_bins", [])
    ]

    bp_data = vis_data.get("box_plot", {})
    box_plot = BoxPlotData(
        min_val=bp_data.get("min_val", 0.0),
        q1=bp_data.get("q1", 0.0),
        median=bp_data.get("median", 0.0),
        q3=bp_data.get("q3", 0.0),
        max_val=bp_data.get("max_val", 0.0),
        target_val=bp_data.get("target_val", 0.0),
    )

    charts = VisualizationData(
        histogram_bins=hist_bins,
        box_plot=box_plot,
        deal_score_breakdown=vis_data.get("deal_score_breakdown", []),
    )

    return OfferAnalysisReport(
        analysis_id=meta.analysis_id,
        target_type="offer",
        started_at=meta.started_at,
        finished_at=meta.finished_at,
        duration_ms=meta.duration_ms,
        framework_version=meta.framework_version,
        cache_used=meta.cache_used,
        target_offer=target_summary,
        similarity=similarity_analysis,
        statistics=price_analysis,
        market_position=market_pos,
        price_efficiency=price_eff,
        offer_quality=offer_qual,
        deal_score=deal_score,
        recommendation=recommendation,
        charts=charts,
    )
