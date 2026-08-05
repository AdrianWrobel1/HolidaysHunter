from abc import ABC, abstractmethod
from typing import Any

from app.providers.schemas import NormalizedOffer


class BaseProvider(ABC):
    """Interface that every tour operator importer must implement.

    A provider is responsible ONLY for:
    - Communicating with the operator's API
    - Handling authentication and pagination
    - Returning raw response data

    A provider must NOT:
    - Write to the database
    - Calculate Travel Score
    - Create price history records
    - Send notifications
    """

    @abstractmethod
    async def fetch_offers(self) -> list[dict[str, Any]]:
        """Fetch raw offer data from the operator's API.

        Returns a list of raw dictionaries exactly as received from the API.
        The normalizer is responsible for mapping these to NormalizedOffer.
        """


class BaseNormalizer(ABC):
    """Interface that maps raw operator data to the normalized Offer format.

    Each operator has different field names, structures, and conventions.
    The normalizer translates operator-specific data into the unified
    NormalizedOffer schema that the rest of the system uses.
    """

    @abstractmethod
    def normalize(self, raw_offer: dict[str, Any]) -> NormalizedOffer | None:
        """Convert a single raw offer dict to a NormalizedOffer.

        Returns None if the raw data is invalid or incomplete and should
        be skipped (the caller will log the skip).
        """
