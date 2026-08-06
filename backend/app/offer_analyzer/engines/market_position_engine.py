"""Market Position Engine using standard Python math."""

from app.analysis_framework import AnalysisContext, BaseAnalysisEngine


class MarketPositionEngine(BaseAnalysisEngine):
    """Engine calculating percentile position and rank relative to market candidates."""

    name = "market_position"
    requires = ["statistics"]
    provides = ["market_position"]

    async def analyze(self, context: AnalysisContext) -> dict:
        stats = context.artifacts.get("statistics", {})
        all_prices = stats.get("all_prices", [])
        target_price = stats.get("target_price", 2000.0)

        if not all_prices:
            all_prices = [target_price]

        total = len(all_prices)

        cheaper_count = sum(1 for p in all_prices if p > target_price)
        more_expensive_count = sum(1 for p in all_prices if p < target_price)

        cheaper_than_pct = (cheaper_count / total * 100.0) if total > 0 else 50.0
        more_exp_pct = (more_expensive_count / total * 100.0) if total > 0 else 50.0

        sorted_prices = sorted(all_prices)
        rank_pos = 1
        for idx, p in enumerate(sorted_prices, start=1):
            if target_price <= p:
                rank_pos = idx
                break

        summary = f"Cena tańsza niż {cheaper_than_pct:.0f}% podobnych ofert rynkowych (Pozycja {rank_pos} z {total})."

        return {
            "cheaper_than_pct": cheaper_than_pct,
            "more_expensive_than_pct": more_exp_pct,
            "price_percentile": 100.0 - cheaper_than_pct,
            "rank_position": rank_pos,
            "total_candidates": total,
            "rank_summary": summary,
        }
