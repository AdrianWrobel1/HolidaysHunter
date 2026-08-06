"""Ranking Engine evaluating and sorting candidate offers across predefined ranking profiles."""

from typing import Any
from app.scoring.config import RANKING_PROFILE_CONFIGS
from app.scoring.deal_score_engine import DealScoreEngine
from app.scoring.explainability import ExplainabilityLayer
from app.scoring.models import RankedOffer, RankingProfile
from app.scoring.value_engine import ValueEngine


class RankingEngine:
    """Ranks candidate offers using DealScore, ValueScore, HotelRating, and Market metrics."""

    def __init__(self) -> None:
        self.deal_engine = DealScoreEngine()
        self.value_engine = ValueEngine()

    def rank_offers(
        self,
        candidate_offers: list[Any],
        profile: RankingProfile = RankingProfile.BEST_DEALS,
        context: dict[str, Any] | None = None,
    ) -> list[RankedOffer]:
        """Compute profile scores and rank offers descending."""
        if not candidate_offers:
            return []

        ctx = context or {}
        profile_config = RANKING_PROFILE_CONFIGS.get(profile, RANKING_PROFILE_CONFIGS[RankingProfile.BEST_DEALS])

        ranked_items: list[tuple[float, Any, int, int, float]] = []

        for cand in candidate_offers:
            val_res = self.value_engine.calculate(cand, ctx)
            deal_res = self.deal_engine.calculate(cand, {**ctx, "value_score": val_res}, diagnostic=False)

            p_score = 0.0
            total_w = 0.0

            # 1. deal_score weight
            if "deal_score" in profile_config:
                w = profile_config["deal_score"]
                p_score += deal_res.total_score * w
                total_w += w

            # 2. value_score weight
            if "value_score" in profile_config:
                w = profile_config["value_score"]
                p_score += val_res.total_score * w
                total_w += w

            # 3. confidence weight
            if "confidence" in profile_config:
                w = profile_config["confidence"]
                p_score += deal_res.confidence.score * w
                total_w += w

            # 4. hotel_stars weight
            if "hotel_stars" in profile_config:
                w = profile_config["hotel_stars"]
                stars = float(getattr(cand, "hotel_stars", 0) or 3.0)
                p_score += (stars / 5.0 * 100.0) * w
                total_w += w

            # 5. guest_rating weight
            if "guest_rating" in profile_config or "hotel_rating" in profile_config:
                w = profile_config.get("guest_rating", profile_config.get("hotel_rating", 0.1))
                rating = float(getattr(cand, "hotel_rating", 0) or 7.5)
                p_score += (rating / 10.0 * 100.0) * w
                total_w += w

            # 6. price_per_person weight (budget)
            if "price_per_person" in profile_config:
                w = profile_config["price_per_person"]
                price = float(getattr(cand, "price_per_person", 0) or 5000.0)
                # Lower price -> higher score (max 100 at 1000 PLN, min 0 at 10000 PLN)
                b_score = max(0.0, min(100.0, 100.0 - (price / 100.0)))
                p_score += b_score * w
                total_w += w

            # Normalize final profile score
            final_prof_score = (p_score / total_w) if total_w > 0 else float(deal_res.total_score)

            ranked_items.append((
                final_prof_score,
                cand,
                deal_res.total_score,
                val_res.total_score,
                deal_res.confidence.score,
            ))

        # Sort descending by profile score
        ranked_items.sort(key=lambda x: x[0], reverse=True)

        results: list[RankedOffer] = []
        for rank_idx, (prof_score, cand, d_score, v_score, conf_pct) in enumerate(ranked_items, start=1):
            cand_id = getattr(cand, "id", None) or getattr(cand, "external_id", "")
            title = getattr(cand, "title", getattr(cand, "hotel_name", "Oferta"))

            rank_exp = ExplainabilityLayer.explain_ranking(profile, rank_idx, prof_score, str(title))

            results.append(RankedOffer(
                offer_id=str(cand_id) if cand_id else None,
                offer_object=cand,
                rank=rank_idx,
                profile=profile,
                score=round(prof_score, 1),
                deal_score=d_score,
                value_score=v_score,
                confidence_pct=round(conf_pct, 1),
                rank_explanation=rank_exp,
            ))

        return results
