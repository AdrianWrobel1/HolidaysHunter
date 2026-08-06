"""Tests for AnalysisContext, ArtifactStore, and AnalysisMetadata."""

import pytest
from app.analysis_framework import AnalysisContext, ArtifactStore, AnalysisMetadata


def test_artifact_store_operations():
    store = ArtifactStore({"initial_key": "initial_value"})
    assert store.has("initial_key")
    assert store.get("initial_key") == "initial_value"

    store.set("statistics", {"mean": 3000})
    assert store["statistics"] == {"mean": 3000}
    assert "statistics" in store

    store["similarity"] = {"score": 95}
    assert store.get("similarity") == {"score": 95}
    assert set(store.list_keys()) == {"initial_key", "statistics", "similarity"}

    exported = store.to_dict()
    assert exported["statistics"] == {"mean": 3000}


def test_analysis_context_initialization():
    ctx = AnalysisContext(target_type="offer")
    assert ctx.target_type == "offer"
    assert isinstance(ctx.artifacts, ArtifactStore)
    assert isinstance(ctx.metadata, AnalysisMetadata)

    ctx.artifacts.set("normalized_offer", {"id": "123"})
    assert ctx.analysis_data.has("normalized_offer")


def test_metadata_lifecycle():
    meta = AnalysisMetadata(target_type="offer", provider="itaka")
    assert meta.target_type == "offer"
    assert meta.provider == "itaka"
    assert meta.finished_at is None

    meta.mark_finished(cache_used=True)
    assert meta.finished_at is not None
    assert meta.duration_ms is not None
    assert meta.cache_used is True
