"""Deterministic Explainability Layer answering 'Dlaczego ta oferta otrzymała taki wynik?'"""

from typing import Any
from app.scoring.models import ComponentResult, DealScore, ValueScore, ConfidenceScore, RankingProfile


class ExplainabilityLayer:
    """Generates human-readable, deterministic explanations from component scoring impacts."""

    @staticmethod
    def explain_value_score(score: float, components: list[ComponentResult]) -> list[str]:
        """Generate deterministic explanations for Value Score."""
        explanations: list[str] = []

        if score >= 80:
            explanations.append("Wyjątkowo wysoki stosunek jakości świadczeń do ceny końcowej.")
        elif score >= 65:
            explanations.append("Bardzo dobra wartość wyjazdu — bogaty pakiet w uczciwej cenie.")
        elif score >= 45:
            explanations.append("Standardowa wartość rynkowa dostosowana do ceny.")
        else:
            explanations.append("Relatywnie niska wartość świadczeń w stosunku do oczekiwanej ceny.")

        # Top positive impacts
        sorted_comps = sorted(components, key=lambda c: c.impact, reverse=True)
        top_pos = [c for c in sorted_comps if c.impact > 1.0][:2]
        top_neg = [c for c in sorted_comps if c.impact < -1.0][-2:]

        for comp in top_pos:
            explanations.append(f"✓ Główny atut: {comp.label} (+{comp.impact:.1f} pkt) — {comp.explanation}")

        for comp in top_neg:
            explanations.append(f"⚠️ Czynnik obniżający: {comp.label} ({comp.impact:.1f} pkt) — {comp.explanation}")

        return explanations

    @staticmethod
    def explain_deal_score(
        total_score: int,
        components: list[ComponentResult],
        confidence: ConfidenceScore | None = None,
    ) -> list[str]:
        """Generate deterministic explanations for Deal Score."""
        explanations: list[str] = []

        if total_score >= 80:
            explanations.append("BARDZO ATRAKCYJNA OKAZJA — rekomendowany zakup w aktualnym momencie.")
        elif total_score >= 65:
            explanations.append("Dobra oferta rynkowa z przewagą punktów w opłacalności.")
        elif total_score >= 45:
            explanations.append("Przeciętna oferta rynkowa bez wyraźnego upustu cenowego.")
        else:
            explanations.append("Niski wskaźnik opłacalności — zalecana ostrożność lub porównanie alternatyw.")

        sorted_comps = sorted(components, key=lambda c: c.impact, reverse=True)
        for comp in sorted_comps:
            if abs(comp.impact) >= 0.5:
                sign = "+" if comp.impact > 0 else ""
                explanations.append(f"{comp.label}: {comp.score:.0f}/100 ({sign}{comp.impact:.1f} pkt do wyniku). {comp.explanation}")

        if confidence:
            explanations.append(f"Pewność wyliczeń: {confidence.score:.0f}% ({confidence.level}) — {', '.join(confidence.explanations)}")

        return explanations

    @staticmethod
    def explain_ranking(
        profile: RankingProfile,
        rank: int,
        score: float,
        offer_title: str,
    ) -> str:
        """Generate deterministic explanation for why an offer holds a specific rank under a profile."""
        profile_names = {
            RankingProfile.BEST_DEALS: "Najlepsze Okazje (Deal Score)",
            RankingProfile.BEST_VALUE: "Najlepsza Wartość (Value Score)",
            RankingProfile.BUDGET: "Oferty Budżetowe",
            RankingProfile.LUXURY: "Luksusowy Standard",
            RankingProfile.FAMILY: "Wyjazd Rodzinny",
            RankingProfile.BEACH: "Wypoczynek Plażowy",
            RankingProfile.LAST_MINUTE: "Last Minute",
        }
        prof_label = profile_names.get(profile, profile.value)
        return f"Oferta '{offer_title}' zajmuje #{rank} miejsce w rankingu '{prof_label}' z wynikiem profilowym {score:.1f}/100."
