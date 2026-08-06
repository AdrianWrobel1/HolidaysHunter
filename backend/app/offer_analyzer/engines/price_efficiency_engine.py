"""Price Efficiency Engine."""

from app.analysis_framework import AnalysisContext, BaseAnalysisEngine


class PriceEfficiencyEngine(BaseAnalysisEngine):
    """Engine computing daily rates and market efficiency ratio."""

    name = "price_efficiency"
    requires = ["statistics"]
    provides = ["price_efficiency"]

    async def analyze(self, context: AnalysisContext) -> dict:
        target = context.analyzed_object
        stats = context.artifacts.get("statistics", {})

        duration = max(1, int(getattr(target, "duration_nights", 7)))
        adults = max(1, int(getattr(target, "adults", 2)))
        target_price = float(getattr(target, "price_per_person", 2000.0))

        daily_rate = target_price / duration
        person_daily_rate = daily_rate / adults if adults > 1 else daily_rate

        mean_price = stats.get("mean_price", target_price)
        mkt_daily = mean_price / duration
        mkt_person_daily = mkt_daily / adults if adults > 1 else mkt_daily

        efficiency_ratio = (mkt_person_daily / person_daily_rate * 100.0) if person_daily_rate > 0 else 100.0
        efficiency_score = max(0.0, min(100.0, efficiency_ratio))

        if efficiency_score >= 110:
            eff_summary = "Bardzo wysoka efektywność kosztowa za dzień pobytu."
        elif efficiency_score >= 90:
            eff_summary = "Optymalna efektywność cenowa."
        else:
            eff_summary = "Wymaga monitorowania pod kątem stawek dziennych."

        return {
            "daily_rate": daily_rate,
            "person_daily_rate": person_daily_rate,
            "market_avg_person_daily_rate": mkt_person_daily,
            "efficiency_score": efficiency_score,
            "summary": eff_summary,
        }
