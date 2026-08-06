"""Similar Offers Analysis Engine."""

from sqlalchemy import select

from app.analysis_framework import AnalysisContext, BaseAnalysisEngine
from app.models.offer import Offer
from app.services.similarity import SimilarityService


class SimilarOffersEngine(BaseAnalysisEngine):
    """Engine finding and ranking similar candidate offers from database."""

    name = "similar_offers"
    requires = []
    provides = ["similarity"]

    async def analyze(self, context: AnalysisContext) -> dict:
        target = context.analyzed_object
        session = context.session
        candidates = context.candidate_objects

        if not candidates and session:
            # Query candidate offers matching country or active status
            stmt = select(Offer).where(Offer.is_available.is_(True)).limit(300)
            res = await session.execute(stmt)
            candidates = list(res.scalars().all())

        similarity_service = SimilarityService()
        ranked_matches = similarity_service.rank_similar_offers(
            target_offer=target,
            candidate_offers=candidates,
            top_k=10,
        )

        similar_items = []
        for m in ranked_matches:
            cand = m.offer_object
            similar_items.append({
                "id": str(getattr(cand, "id", "")) if getattr(cand, "id", None) else None,
                "external_id": getattr(cand, "external_id", "ext-id"),
                "provider": str(getattr(cand, "provider", "itaka")),
                "title": getattr(cand, "title", "Oferta"),
                "hotel_name": getattr(cand, "hotel_name", "Hotel"),
                "country": getattr(cand, "country", ""),
                "region": getattr(cand, "region", None),
                "hotel_stars": float(getattr(cand, "hotel_stars", 0) or 0),
                "departure_date": getattr(cand, "departure_date", target.departure_date),
                "duration_nights": int(getattr(cand, "duration_nights", 7)),
                "meal_type": str(getattr(cand, "meal_type", "all_inclusive")),
                "departure_city": getattr(cand, "departure_city", "Warszawa"),
                "price_per_person": float(getattr(cand, "price_per_person", 0)),
                "similarity_score": m.similarity_score,
                "explanations": m.explanations,
                "offer_url": getattr(cand, "offer_url", None),
                "transport_type": str(getattr(cand, "transport_type", "flight")),
            })

        return {
            "candidates_count": len(candidates),
            "top_matches": similar_items,
            "similar_offers": similar_items,
        }
