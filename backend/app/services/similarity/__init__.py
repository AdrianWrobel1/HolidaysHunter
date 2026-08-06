"""Standalone Similarity Service package."""

from app.services.similarity.config import DEFAULT_SIMILARITY_WEIGHTS
from app.services.similarity.service import SimilarityMatchResult, SimilarityService

__all__ = [
    "SimilarityService",
    "SimilarityMatchResult",
    "DEFAULT_SIMILARITY_WEIGHTS",
]
