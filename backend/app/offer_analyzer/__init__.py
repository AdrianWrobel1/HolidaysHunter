"""Offer Analyzer module built on top of Universal Analysis Framework."""

from app.offer_analyzer.models import OfferAnalyzeRequest, OfferAnalysisReport
from app.offer_analyzer.parser import detect_provider_from_url, parse_offer_from_url
from app.offer_analyzer.service import analyze_offer_url

__all__ = [
    "OfferAnalyzeRequest",
    "OfferAnalysisReport",
    "detect_provider_from_url",
    "parse_offer_from_url",
    "analyze_offer_url",
]
