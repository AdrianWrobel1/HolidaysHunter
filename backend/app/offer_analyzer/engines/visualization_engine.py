"""Visualization Engine for calculating pre-binned chart data using standard library math."""

import math

from app.analysis_framework import AnalysisContext, BaseAnalysisEngine


class VisualizationEngine(BaseAnalysisEngine):
    """Engine generating pre-calculated chart structures for frontend visual components."""

    name = "visualization"
    requires = ["statistics", "similarity", "deal_score", "market_position"]
    provides = ["visualization"]

    async def analyze(self, context: AnalysisContext) -> dict:
        stats = context.artifacts.get("statistics", {})
        deal_score_data = context.artifacts.get("deal_score", {})

        all_prices = stats.get("all_prices", [2000.0])
        target_price = stats.get("target_price", 2000.0)

        min_p = min(all_prices) if all_prices else 1000.0
        max_p = max(all_prices) if all_prices else 3000.0

        num_bins = 6
        if max_p == min_p:
            bin_edges = [min_p - 100, max_p + 100]
        else:
            step = (max_p - min_p) / num_bins
            bin_edges = [min_p + i * step for i in range(num_bins + 1)]

        histogram_bins = []
        for i in range(len(bin_edges) - 1):
            b_min = bin_edges[i]
            b_max = bin_edges[i + 1]

            if i == len(bin_edges) - 2:
                count = sum(1 for p in all_prices if b_min <= p <= b_max)
                is_target = (b_min <= target_price <= b_max)
            else:
                count = sum(1 for p in all_prices if b_min <= p < b_max)
                is_target = (b_min <= target_price < b_max)

            histogram_bins.append({
                "bin_label": f"{b_min:.0f} - {b_max:.0f} zł",
                "bin_min": round(b_min, 1),
                "bin_max": round(b_max, 1),
                "count": count,
                "is_target_bin": is_target,
            })

        box_plot = {
            "min_val": float(stats.get("min_price", min_p)),
            "q1": float(stats.get("percentile_25", min_p)),
            "median": float(stats.get("median_price", (min_p + max_p) / 2)),
            "q3": float(stats.get("percentile_75", max_p)),
            "max_val": float(stats.get("max_price", max_p)),
            "target_val": target_price,
        }

        deal_components = deal_score_data.get("components", [])

        return {
            "histogram_bins": histogram_bins,
            "box_plot": box_plot,
            "deal_score_breakdown": deal_components,
        }
