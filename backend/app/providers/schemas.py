import logging
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import MealType, Provider, TransportType

logger = logging.getLogger(__name__)


class NormalizedOffer(BaseModel):
    """Unified offer schema that every provider normalizer must produce.

    This is the contract between the provider layer and the persistence layer.
    All fields use domain types — no raw strings for enums.
    """

    external_id: str
    provider: Provider

    title: str
    country: str
    region: str | None = None
    city: str | None = None

    hotel_name: str
    hotel_stars: float | None = None
    hotel_rating: float | None = None

    departure_date: date
    return_date: date
    duration_nights: int

    departure_city: str

    adults: int
    children: int = 0

    meal_type: MealType
    transport_type: TransportType

    price_total: Decimal = Field(ge=0)
    price_per_person: Decimal = Field(ge=0)
    currency: str = "PLN"

    offer_url: str | None = None
    image_url: str | None = None


PROVIDER_DOMAINS: dict[str, str] = {
    "itaka": "https://www.itaka.pl",
    "tui": "https://www.tui.pl",
    "rainbow": "https://r.pl",
    "wakacje_pl": "https://www.wakacje.pl",
}


def build_direct_offer_url(
    provider: Provider | str,
    external_id: str,
    raw_url: str | None = None,
) -> str | None:
    """Resolve direct offer deep link for a provider.

    Behavior:
    - If raw_url is full URL (http:// or https://), return it directly.
    - If raw_url is relative path, prepend provider domain.
    - If raw_url is missing or empty, log detailed warning and return None.
      NO fallbacks (no Google Search, no search query, no region pages, no homepage).
    """
    prov_str = provider.value if isinstance(provider, Provider) else str(provider).lower()

    if not raw_url or not str(raw_url).strip():
        logger.warning(
            "Provider [%s] offer [%s]: missing direct offer URL in API response.",
            prov_str.upper(),
            external_id,
        )
        return None

    clean_url = str(raw_url).strip()

    if clean_url.startswith("http://") or clean_url.startswith("https://"):
        return clean_url

    domain = PROVIDER_DOMAINS.get(prov_str)
    if domain:
        return f"{domain}{clean_url if clean_url.startswith('/') else '/' + clean_url}"

    logger.warning(
        "Provider [%s] offer [%s]: unrecognized URL format '%s' without known domain mapping.",
        prov_str.upper(),
        external_id,
        clean_url,
    )
    return None
