"""Deterministic Recommendation Engine."""

from app.analysis_framework import AnalysisContext, BaseAnalysisEngine


class RecommendationEngine(BaseAnalysisEngine):
    """Engine executing deterministic business rule evaluation for offer recommendations."""

    name = "recommendation"
    requires = ["deal_score", "statistics", "market_position"]
    provides = ["recommendation"]

    async def analyze(self, context: AnalysisContext) -> dict:
        deal_score_data = context.artifacts.get("deal_score", {})
        stats = context.artifacts.get("statistics", {})
        market = context.artifacts.get("market_position", {})

        total_score = deal_score_data.get("total_score", 50)
        diff_pct = stats.get("price_diff_pct", 0.0)
        cheaper_than_pct = market.get("cheaper_than_pct", 50.0)

        takeaways = []

        if total_score >= 80:
            badge = "EXCELLENT DEAL"
            color = "emerald"
            title = "Wyjątkowa okazja rynkowa"
            takeaways.append("Cena znacząco poniżej średniej rynkowej dla tego standardu.")
            takeaways.append(f"Oferta jest tańsza niż {cheaper_than_pct:.0f}% porównywalnych wyjazdów.")
            takeaways.append("Wysoki wskaźnik opłacalności dziennej i świetne oceny hotelu.")
        elif total_score >= 65:
            badge = "VERY COMPETITIVE"
            color = "indigo"
            title = "Bardzo atrakcyjna oferta"
            takeaways.append("Cena bardziej konkurencyjna niż większość ofert w tym regionie.")
            takeaways.append("Zbalansowany stosunek ceny do jakości wyżywienia i standardu.")
            takeaways.append("Warta rozważenia szybka rezerwacja.")
        elif total_score >= 50:
            badge = "AVERAGE OFFER"
            color = "amber"
            title = "Standardowa oferta rynkowa"
            takeaways.append("Cena oscyluje wokół średniej rynkowej.")
            takeaways.append("Rekomendowane dalsze obserwowanie zmian cenowych.")
            takeaways.append("Dobry wybór jeśli priorytetem jest konkretny termin lub hotel.")
        else:
            badge = "ABOVE MARKET AVERAGE"
            color = "rose"
            title = "Wysoka cena w stosunku do rynku"
            takeaways.append("Cena powyżej średniej dla tego standardu i długości pobytu.")
            takeaways.append(f"Większość ofert rynkowych ({100 - cheaper_than_pct:.0f}%) jest tańsza.")
            takeaways.append("Zalecane poszukiwanie alternatywnych terminów lub hoteli.")

        return {
            "verdict_badge": badge,
            "verdict_color": color,
            "title": title,
            "takeaways": takeaways,
        }
