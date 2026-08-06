"""Deal Score Engine wrapping shared app.scoring DealScoreEngine."""

from app.analysis_framework import AnalysisContext, BaseAnalysisEngine
from app.scoring import DealScoreEngine as SharedDealScoreEngine


class DealScoreEngine(BaseAnalysisEngine):
    """Engine executing the shared modular Deal Score framework."""

    name = "deal_score"
    requires = ["statistics", "similarity", "market_position", "offer_quality"]
    provides = ["deal_score"]

    async def analyze(self, context: AnalysisContext) -> dict:
        shared_engine = SharedDealScoreEngine()

        # Build market & statistics context dictionary
        scoring_ctx = {
            "statistics": context.artifacts.get("statistics", {}),
            "market_position": context.artifacts.get("market_position", {}),
            "candidates_count": len(context.candidate_objects),
            "price_history": context.artifacts.get("price_history", []),
        }

        deal_res = shared_engine.calculate(
            offer=context.analyzed_object,
            context=scoring_ctx,
            diagnostic=True,
        )

        component_list = []
        for comp in deal_res.components:
            component_list.append({
                "name": comp.name,
                "score": comp.score,
                "weight": comp.weight,
                "weighted_score": comp.weighted_score,
                "explanation": comp.explanation,
                "impact": comp.impact,
            })

        return {
            "total_score": deal_res.total_score,
            "raw_score": deal_res.raw_score,
            "summary": deal_res.summary,
            "value_score": deal_res.value_score,
            "confidence": deal_res.confidence.model_dump(),
            "components": component_list,
            "explanations": deal_res.explanations,
            "diagnostic_details": deal_res.diagnostic_details,
        }
