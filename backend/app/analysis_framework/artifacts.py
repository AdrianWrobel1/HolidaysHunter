"""Artifact Store for storing intermediate and final analysis artifacts."""

from typing import Any


class ArtifactStore:
    """Centralized repository storing all artifacts produced during analysis."""

    def __init__(self, initial_data: dict[str, Any] | None = None) -> None:
        self._store: dict[str, Any] = initial_data.copy() if initial_data else {}

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve an artifact by key."""
        return self._store.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store an artifact under a key."""
        self._store[key] = value

    def has(self, key: str) -> bool:
        """Check if an artifact exists in the store."""
        return key in self._store

    def list_keys(self) -> list[str]:
        """Return list of all artifact keys."""
        return list(self._store.keys())

    def to_dict(self) -> dict[str, Any]:
        """Export all artifacts as a shallow copy dictionary."""
        return self._store.copy()

    def __getitem__(self, key: str) -> Any:
        if key not in self._store:
            raise KeyError(f"Artifact '{key}' not found in ArtifactStore.")
        return self._store[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        return self.has(key)
