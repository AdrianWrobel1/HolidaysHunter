"""Price Statistics Engine using Python standard library math."""

import math
import statistics

from app.analysis_framework import AnalysisContext, BaseAnalysisEngine


class PriceStatisticsEngine(BaseAnalysisEngine):
    """Engine computing min, max, mean, median, std_dev, percentiles, price/day, price/person/day."""

    name = "statistics"
    requires = ["similarity"]
    provides = ["statistics"]

    async def analyze(self, context: AnalysisContext) -> dict:
        target = context.analyzed_object
        similarity_data = context.artifacts.get("similarity", {})
        top_matches = similarity_data.get("similar_offers", [])

        target_price = float(getattr(target, "price_per_person", 2000.0))
        duration = max(1, int(getattr(target, "duration_nights", 7)))

        prices = [float(o["price_per_person"]) for o in top_matches if float(o.get("price_per_person", 0)) > 0]
        if not prices:
            prices = [target_price]

        prices.sort()

        min_val = min(prices)
        max_val = max(prices)
        mean_val = statistics.mean(prices)
        median_val = statistics.median(prices)
        std_val = statistics.stdev(prices) if len(prices) > 1 else 0.0

        p25_val = self._percentile(prices, 25)
        p75_val = self._percentile(prices, 75)

        price_per_day = target_price / duration
        price_per_person_per_day = target_price / duration

        diff_amt = target_price - mean_val
        diff_pct = (diff_amt / mean_val * 100.0) if mean_val > 0 else 0.0

        if diff_pct < -15:
            pos_summary = f"Cena aktualna jest o {abs(diff_pct):.1f}% NIŻSZA niż średnia rynkowa."
        elif diff_pct > 15:
            pos_summary = f"Cena aktualna jest o {diff_pct:.1f}% WYŻSZA niż średnia rynkowa."
        else:
            pos_summary = "Cena zbliżona do średniej rynkowej."

        return {
            "min_price": min_val,
            "max_price": max_val,
            "mean_price": mean_val,
            "mean_price_per_person": mean_val,
            "median_price": median_val,
            "std_dev": std_val,
            "percentile_25": p25_val,
            "percentile_75": p75_val,
            "target_price": target_price,
            "price_per_day": price_per_day,
            "price_per_person_per_day": price_per_person_per_day,
            "price_diff_amount": diff_amt,
            "price_diff_pct": diff_pct,
            "position_summary": pos_summary,
            "all_prices": prices,
        }

    @staticmethod
    def _percentile(data: list[float], percentile: float) -> float:
        if not data:
            return 0.0
        n = len(data)
        if n == 1:
            return data[0]
        k = (n - 1) * (percentile / 100.0)
        f = math.floor(k)
        c = math.ceil(k)
        if f == c:
            return data[int(k)]
        d0 = data[int(f)] * (c - k)
        d1 = data[int(c)] * (k - f)
        return d0 + d1
