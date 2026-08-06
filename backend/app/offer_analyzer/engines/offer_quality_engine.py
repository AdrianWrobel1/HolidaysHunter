"""Offer Quality Engine."""

from app.analysis_framework import AnalysisContext, BaseAnalysisEngine


class OfferQualityEngine(BaseAnalysisEngine):
    """Engine computing offer data quality index and completeness highlights."""

    name = "offer_quality"
    requires = []
    provides = ["offer_quality"]

    async def analyze(self, context: AnalysisContext) -> dict:
        target = context.analyzed_object
        highlights = []

        stars = float(getattr(target, "hotel_stars", 0) or 0)
        rating = float(getattr(target, "hotel_rating", 0) or 0)
        meal = str(getattr(target, "meal_type", "")).lower()
        img = getattr(target, "image_url", None)
        url = getattr(target, "offer_url", None)

        score = 50.0

        if stars >= 4.0:
            score += 20.0
            highlights.append(f"Wysoki standard hotelu ({stars:.0f}★)")

        if rating >= 8.5:
            score += 15.0
            highlights.append(f"Świetne opinie gości ({rating}/10)")

        if "all" in meal:
            score += 10.0
            highlights.append("Pełny pakiet All Inclusive")

        if img:
            score += 5.0
            highlights.append("Zweryfikowana galeria zdjęć")

        if url:
            score += 5.0
            highlights.append("Bezpośredni link do rezerwacji")

        quality_score = max(0.0, min(100.0, score))

        fields = [
            "title", "country", "region", "city", "hotel_name",
            "hotel_stars", "departure_date", "return_date",
            "departure_city", "meal_type", "price_per_person",
            "offer_url", "image_url"
        ]
        present = sum(1 for f in fields if getattr(target, f, None) is not None)
        completeness = (present / len(fields)) * 100.0

        return {
            "quality_score": quality_score,
            "completeness_pct": completeness,
            "highlights": highlights,
        }
