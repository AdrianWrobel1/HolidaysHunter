"""Standalone Similarity Service reusable across search, rankings, alerts, and recommendations."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from app.services.similarity.config import DEFAULT_SIMILARITY_WEIGHTS


@dataclass
class SimilarityMatchResult:
    """Result of a pairwise similarity comparison."""

    offer_id: str | None
    offer_object: Any
    similarity_score: float  # 0 to 100
    explanations: list[str] = field(default_factory=list)
    feature_scores: dict[str, float] = field(default_factory=dict)


class SimilarityService:
    """Calculates weighted similarity score and generates human-readable explanations."""

    def __init__(self, feature_weights: dict[str, float] | None = None) -> None:
        self.weights = feature_weights or DEFAULT_SIMILARITY_WEIGHTS

    def calculate_similarity(
        self,
        target_offer: Any,
        candidate_offer: Any,
    ) -> SimilarityMatchResult:
        """Compute pairwise similarity between target offer and candidate offer."""
        scores: dict[str, float] = {}
        explanations: list[str] = []

        # 1. Hotel name similarity
        h1 = str(getattr(target_offer, "hotel_name", "") or "").strip().lower()
        h2 = str(getattr(candidate_offer, "hotel_name", "") or "").strip().lower()
        if h1 and h2 and (h1 == h2 or h1 in h2 or h2 in h1):
            scores["hotel_name"] = 1.0
            explanations.append("✓ Ten sam hotel")
        else:
            scores["hotel_name"] = 0.0

        # 2. Country similarity
        c1 = str(getattr(target_offer, "country", "") or "").strip().lower()
        c2 = str(getattr(candidate_offer, "country", "") or "").strip().lower()
        if c1 and c2 and c1 == c2:
            scores["country"] = 1.0
            explanations.append(f"✓ Ten sam kraj ({getattr(target_offer, 'country', '')})")
        else:
            scores["country"] = 0.0

        # 3. Region similarity
        r1 = str(getattr(target_offer, "region", "") or "").strip().lower()
        r2 = str(getattr(candidate_offer, "region", "") or "").strip().lower()
        if r1 and r2 and r1 == r2:
            scores["region"] = 1.0
            explanations.append("✓ Ten sam region")
        else:
            scores["region"] = 0.0

        # 4. City similarity
        ct1 = str(getattr(target_offer, "city", "") or "").strip().lower()
        ct2 = str(getattr(candidate_offer, "city", "") or "").strip().lower()
        if ct1 and ct2 and ct1 == ct2:
            scores["city"] = 1.0
            explanations.append("✓ Ta sama miejscowość")
        else:
            scores["city"] = 0.0

        # 5. Hotel stars
        s1 = float(getattr(target_offer, "hotel_stars", 0) or 0)
        s2 = float(getattr(candidate_offer, "hotel_stars", 0) or 0)
        if s1 > 0 and s2 > 0:
            diff = abs(s1 - s2)
            star_score = max(0.0, 1.0 - (diff / 3.0))
            scores["hotel_stars"] = star_score
            if diff == 0:
                explanations.append(f"✓ Identyczny standard ({s1:.0f}★)")
        else:
            scores["hotel_stars"] = 0.5

        # 6. Duration nights
        d1 = int(getattr(target_offer, "duration_nights", 0) or 0)
        d2 = int(getattr(candidate_offer, "duration_nights", 0) or 0)
        if d1 > 0 and d2 > 0:
            diff = abs(d1 - d2)
            dur_score = max(0.0, 1.0 - (diff / 7.0))
            scores["duration_nights"] = dur_score
            if diff == 0:
                explanations.append(f"✓ Taka sama długość pobytu ({d1} dni)")
            elif diff <= 2:
                explanations.append(f"✓ Zbliżona długość pobytu (różnica {diff} dni)")
        else:
            scores["duration_nights"] = 0.5

        # 7. Departure date window
        dt1 = getattr(target_offer, "departure_date", None)
        dt2 = getattr(candidate_offer, "departure_date", None)
        if isinstance(dt1, date) and isinstance(dt2, date):
            days_diff = abs((dt1 - dt2).days)
            date_score = max(0.0, 1.0 - (days_diff / 14.0))
            scores["departure_date"] = date_score
            if days_diff == 0:
                explanations.append("✓ Identyczny termin wyjazdu")
            elif days_diff <= 3:
                explanations.append(f"✓ Wyjazd ±{days_diff} dni")
        else:
            scores["departure_date"] = 0.5

        # 8. Meal type
        m1 = str(getattr(target_offer, "meal_type", "") or "").strip().lower()
        m2 = str(getattr(candidate_offer, "meal_type", "") or "").strip().lower()
        if m1 and m2 and m1 == m2:
            scores["meal_type"] = 1.0
            explanations.append("✓ Identyczne wyżywienie")
        else:
            scores["meal_type"] = 0.0

        # 9. Departure city
        dc1 = str(getattr(target_offer, "departure_city", "") or "").strip().lower()
        dc2 = str(getattr(candidate_offer, "departure_city", "") or "").strip().lower()
        if dc1 and dc2 and dc1 == dc2:
            scores["departure_city"] = 1.0
            explanations.append(f"✓ Wylot z {getattr(target_offer, 'departure_city', '')}")
        else:
            scores["departure_city"] = 0.0

        # 10. Price similarity
        p1 = float(getattr(target_offer, "price_per_person", 0) or 0)
        p2 = float(getattr(candidate_offer, "price_per_person", 0) or 0)
        if p1 > 0 and p2 > 0:
            price_ratio = min(p1, p2) / max(p1, p2)
            scores["price"] = price_ratio
            if price_ratio >= 0.9:
                explanations.append("✓ Bardzo zbliżona cena")
        else:
            scores["price"] = 0.5

        # 11. Transport type
        tt1 = getattr(target_offer, "transport_type", "flight")
        tt2 = getattr(candidate_offer, "transport_type", "flight")
        tt1_str = tt1.value if hasattr(tt1, "value") else str(tt1).lower()
        tt2_str = tt2.value if hasattr(tt2, "value") else str(tt2).lower()
        
        if tt1_str == tt2_str:
            scores["transport_type"] = 1.0
            explanations.append(f"✓ Ten sam typ transportu ({tt1_str.upper()})")
        else:
            scores["transport_type"] = 0.0
            explanations.append(f"✗ Różny typ transportu ({tt1_str.upper()} vs {tt2_str.upper()})")

        # Calculate final weighted score
        total_w = 0.0
        weighted_sum = 0.0
        for feat, weight in self.weights.items():
            f_score = scores.get(feat, 0.5)
            weighted_sum += f_score * weight
            total_w += weight

        final_pct = (weighted_sum / total_w) * 100.0 if total_w > 0 else 50.0

        # Apply mismatch penalty if transport types differ (e.g. Flight vs Self Transport)
        if tt1_str != tt2_str:
            final_pct *= 0.75  # 25% penalty for transport mismatch

        cand_id = getattr(candidate_offer, "id", None) or getattr(candidate_offer, "external_id", None)

        return SimilarityMatchResult(
            offer_id=str(cand_id) if cand_id else None,
            offer_object=candidate_offer,
            similarity_score=round(final_pct, 1),
            explanations=explanations,
            feature_scores=scores,
        )

    def rank_similar_offers(
        self,
        target_offer: Any,
        candidate_offers: list[Any],
        top_k: int = 10,
    ) -> list[SimilarityMatchResult]:
        """Rank candidate offers by similarity score descending."""
        results = [
            self.calculate_similarity(target_offer, cand)
            for cand in candidate_offers
        ]
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        return results[:top_k]
