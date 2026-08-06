"""Confidence Engine calculating data certainty (0-100%) to answer 'Na ile możemy ufać wyliczeniom?'"""

from typing import Any
from app.scoring.models import ConfidenceScore


class ConfidenceEngine:
    """Evaluates data density, market sample size, price history, and completeness."""

    def calculate(self, offer: Any, context: dict[str, Any] | None = None) -> ConfidenceScore:
        ctx = context or {}

        # 1. Market sample size
        candidates = ctx.get("candidates_count", 0)
        if candidates >= 50:
            sample_pts = 40.0
            sample_exp = f"Baza rynkowa: {candidates} ofert"
        elif candidates >= 10:
            sample_pts = 25.0
            sample_exp = f"Baza rynkowa: {candidates} ofert (umiarkowana wielkość)"
        else:
            sample_pts = 10.0
            sample_exp = f"Ograniczona baza porównawcza: {candidates} ofert"

        # 2. Price history availability
        price_history = ctx.get("price_history", [])
        has_history = len(price_history) > 1
        if len(price_history) >= 5:
            hist_pts = 30.0
            hist_exp = f"Baza historii cen: {len(price_history)} wpisów"
        elif has_history:
            hist_pts = 20.0
            hist_exp = "Krótka historia cenowa"
        else:
            hist_pts = 5.0
            hist_exp = "Brak zarejestrowanej historii cen"

        # 3. Completeness of key target offer fields
        required = ["price_per_person", "hotel_stars", "hotel_rating", "departure_date", "meal_type", "transport_type"]
        present = sum(1 for f in required if getattr(offer, f, None) is not None)
        comp_pct = (present / len(required)) * 100.0
        comp_pts = (comp_pct / 100.0) * 30.0

        total_pct = sample_pts + hist_pts + comp_pts
        clamped_score = max(0.0, min(100.0, total_pct))

        if clamped_score >= 80:
            level = "HIGH"
        elif clamped_score >= 50:
            level = "MEDIUM"
        else:
            level = "LOW"

        explanations = [sample_exp, hist_exp, f"Kompletność pól oferty: {comp_pct:.0f}%"]

        return ConfidenceScore(
            score=round(clamped_score, 1),
            level=level,
            data_points_count=candidates,
            has_price_history=has_history,
            completeness_pct=round(comp_pct, 1),
            explanations=explanations,
        )
