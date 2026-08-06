import hashlib
import logging
import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import parse_qs, urlparse

from app.core.countries import normalize_country_name
from app.models.enums import MealType, Provider, TransportType
from app.providers.base import BaseNormalizer
from app.providers.schemas import NormalizedOffer, build_direct_offer_url

logger = logging.getLogger(__name__)


def _parse_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except (ValueError, TypeError):
        return None


MEAL_TYPE_MAP: dict[str, MealType] = {
    "all_inclusive": MealType.ALL_INCLUSIVE,
    "all inclusive": MealType.ALL_INCLUSIVE,
    "all-inclusive": MealType.ALL_INCLUSIVE,
    "ai": MealType.ALL_INCLUSIVE,
    "full_board": MealType.FULL_BOARD,
    "full board": MealType.FULL_BOARD,
    "fb": MealType.FULL_BOARD,
    "half_board": MealType.HALF_BOARD,
    "half board": MealType.HALF_BOARD,
    "hb": MealType.HALF_BOARD,
    "bed_and_breakfast": MealType.BED_AND_BREAKFAST,
    "bed and breakfast": MealType.BED_AND_BREAKFAST,
    "bb": MealType.BED_AND_BREAKFAST,
    "self_catering": MealType.SELF_CATERING,
    "self catering": MealType.SELF_CATERING,
    "sc": MealType.SELF_CATERING,
    "ov": MealType.SELF_CATERING,
    "own": MealType.SELF_CATERING,
    "bez wyżywienia": MealType.SELF_CATERING,
    "śniadania": MealType.BED_AND_BREAKFAST,
    "śniadania i obiadokolacje": MealType.HALF_BOARD,
    "pełne wyżywienie": MealType.FULL_BOARD,
}


def _resolve_meal_type(raw: str | None) -> MealType:
    if not raw:
        return MealType.HALF_BOARD
    cleaned = raw.lower().strip()
    try:
        return MealType(cleaned)
    except ValueError:
        pass
    return MEAL_TYPE_MAP.get(cleaned, MealType.HALF_BOARD)


def _extract_external_id(raw_offer: dict[str, Any], raw_url: str | None) -> str | None:
    """Extract a deterministic, stable external_id for a Rainbow offer.

    Hierarchy:
    1. Explicit identifier fields (id, external_id, kodOferty, offerId, @id, sku, productID, identifier, gtin).
    2. URL query parameters (unikalnyKluczOferty, kodOferty, id, offerId, sku).
    3. URL path / slug identifier (e.g. 'hiszpania-costa-del-sol-wczasy/playacalida' -> 'rpl:hiszpania-costa-del-sol-wczasy:playacalida').
    4. Image URL asset ID (e.g. 'grafiki.r.pl/hotel/728/...' -> 'rpl:hotel:728').
    5. Attribute signature hash (SHA-256 of normalized country:region:hotel_name:duration).

    Note: When package identity fields (departure date, city, duration, meal type) are explicitly provided
    in raw_offer or URL query parameters, they are appended to ensure distinct departures produce distinct IDs,
    while price variations preserve the exact same ID.
    """
    # 1. Explicit ID fields
    explicit_keys = [
        "id",
        "external_id",
        "externalId",
        "kodOferty",
        "offerId",
        "@id",
        "sku",
        "productID",
        "identifier",
        "gtin",
    ]
    for k in explicit_keys:
        val = raw_offer.get(k)
        if val is not None and str(val).strip():
            return str(val).strip()

    # 2. Query parameters in raw_url
    parsed_url = urlparse(raw_url) if raw_url else urlparse("")
    params = parse_qs(parsed_url.query)
    for q_param in ["unikalnyKluczOferty", "kodOferty", "id", "offerId", "sku"]:
        key_list = params.get(q_param, [])
        if key_list and str(key_list[0]).strip():
            return str(key_list[0]).strip()

    # Extract non-price package identity modifiers if explicitly present
    pkg_parts = []
    dep_date = raw_offer.get("dataWyjazdu") or raw_offer.get("departureDate") or (params.get("od", [None])[0])
    dep_city = raw_offer.get("miastoWylotu") or raw_offer.get("departureCity") or (params.get("wylot", [None])[0])
    dur = raw_offer.get("liczbaNocy") or raw_offer.get("duration") or (params.get("nocy", [None])[0])
    meal = raw_offer.get("wyzywienie") or raw_offer.get("mealType") or raw_offer.get("boardType") or (params.get("wyzywienie", [None])[0])

    if dep_date:
        pkg_parts.append(str(dep_date)[:10])
    if dep_city:
        pkg_parts.append(str(dep_city).strip().lower())
    if dur:
        pkg_parts.append(f"{dur}n")
    if meal:
        pkg_parts.append(str(meal).strip().lower())

    pkg_suffix = (":" + ":".join(pkg_parts)) if pkg_parts else ""

    # 3. Canonical URL path slug
    path = parsed_url.path.strip("/")
    if path:
        slug_parts = [p for p in path.split("/") if p]
        if slug_parts and not (len(slug_parts) == 1 and slug_parts[0] in ("szukaj", "search")):
            clean_slug = ":".join(slug_parts)
            return f"rpl:{clean_slug}{pkg_suffix}"

    # 4. Image URL asset ID
    image_url = raw_offer.get("zdjecieGlowne") or raw_offer.get("imageUrl") or raw_offer.get("image")
    if image_url:
        match = re.search(r'/hotel/(\d+)/', str(image_url))
        if match:
            return f"rpl:hotel:{match.group(1)}{pkg_suffix}"

    # 5. Deterministic hash signature of offer attributes as fallback
    name = (
        raw_offer.get("nazwaHotelu")
        or raw_offer.get("hotelName")
        or raw_offer.get("tytul")
        or raw_offer.get("title")
        or raw_offer.get("name")
        or ""
    ).strip().lower()
    country = str(raw_offer.get("kraj") or raw_offer.get("country") or "").strip().lower()
    region = str(raw_offer.get("region") or "").strip().lower()
    duration = str(raw_offer.get("liczbaNocy") or raw_offer.get("duration") or "7").strip()

    if name or country:
        sig = f"{country}:{region}:{name}:{duration}{pkg_suffix}"
        hash_hex = hashlib.sha256(sig.encode("utf-8")).hexdigest()[:16]
        return f"rpl:hash:{hash_hex}"

    return None


class RainbowNormalizer(BaseNormalizer):
    """Maps Rainbow application/ld+json Product to NormalizedOffer schema."""

    def normalize(self, raw_offer: dict[str, Any]) -> NormalizedOffer | None:
        raw_url = raw_offer.get("url") or raw_offer.get("OfertaUrl") or raw_offer.get("ofertaUrl") or raw_offer.get("offerUrl")

        offer_id = _extract_external_id(raw_offer, raw_url)
        if not offer_id:
            logger.warning("Rainbow: skipping offer without valid external_id")
            return None

        offers_dict = raw_offer.get("offers", {})
        price_raw = (
            (offers_dict.get("price") if isinstance(offers_dict, dict) else None)
            or raw_offer.get("cenaCalkowita")
            or raw_offer.get("priceTotal")
            or raw_offer.get("price")
        )
        price_total = _parse_decimal(price_raw)
        if price_total is None or price_total <= 0:
            logger.warning("Rainbow: skipping offer %s — invalid price", offer_id)
            return None

        adults = raw_offer.get("dorosli") or raw_offer.get("adults") or 2
        children = raw_offer.get("dzieci") or raw_offer.get("children") or 0

        ppp_raw = raw_offer.get("cenaZaOsobe") or raw_offer.get("pricePerPerson")
        price_per_person = (
            _parse_decimal(ppp_raw)
            if ppp_raw is not None
            else ((price_total / adults).quantize(Decimal("0.01")) if adults > 0 else price_total)
        )

        name = (
            raw_offer.get("nazwaHotelu")
            or raw_offer.get("hotelName")
            or raw_offer.get("tytul")
            or raw_offer.get("title")
            or raw_offer.get("name", "Wycieczka Rainbow")
        )
        title = raw_offer.get("tytul") or raw_offer.get("title") or name
        description = raw_offer.get("description", "")

        # Extract country/region from description (e.g. "Wypoczynek • Hiszpania: Costa del Sol")
        raw_country = raw_offer.get("kraj") or raw_offer.get("country") or "Grecja"
        region = raw_offer.get("region")
        if ":" in description:
            parts = description.split(":", 1)
            raw_country = parts[0].split("•")[-1].strip()
            if not region:
                region = parts[1].strip()
        elif "•" in description and not raw_offer.get("country"):
            raw_country = description.split("•")[-1].strip()

        country = normalize_country_name(raw_country)
        if region and region.lower() == country.lower():
            region = None

        # Dates default to upcoming season if not in raw offer
        departure_date = _parse_date(raw_offer.get("dataWyjazdu") or raw_offer.get("departureDate"))
        if departure_date is None:
            departure_date = date.today() + timedelta(days=30)
        duration = int(raw_offer.get("liczbaNocy") or raw_offer.get("duration") or 7)
        return_date = _parse_date(raw_offer.get("dataPowrotu") or raw_offer.get("returnDate")) or (
            departure_date + timedelta(days=duration)
        )

        offer_url = build_direct_offer_url(Provider.RAINBOW, str(offer_id), raw_url)
        image_url = raw_offer.get("zdjecieGlowne") or raw_offer.get("imageUrl") or raw_offer.get("image")

        stars_raw = raw_offer.get("standardHotelu") or raw_offer.get("hotelStars")
        hotel_stars: float | None = float(stars_raw) if stars_raw is not None else None

        rating_raw = raw_offer.get("ocenaHotelu") or raw_offer.get("hotelRating")
        if rating_raw is None and isinstance(raw_offer.get("aggregateRating"), dict):
            rating_raw = raw_offer["aggregateRating"].get("ratingValue")
        hotel_rating: float | None = float(rating_raw) if rating_raw is not None else None

        meal_raw = raw_offer.get("wyzywienie") or raw_offer.get("mealType") or raw_offer.get("boardType")

        return NormalizedOffer(
            external_id=str(offer_id),
            provider=Provider.RAINBOW,
            title=title,
            country=country,
            region=region,
            city=raw_offer.get("miasto") or raw_offer.get("city") or region,
            hotel_name=name,
            hotel_stars=hotel_stars,
            hotel_rating=hotel_rating,
            departure_date=departure_date,
            return_date=return_date,
            duration_nights=duration,
            departure_city=raw_offer.get("miastoWylotu") or raw_offer.get("departureCity") or "Warszawa",
            adults=adults,
            children=children,
            meal_type=_resolve_meal_type(meal_raw),
            transport_type=TransportType.FLIGHT,
            price_total=price_total,
            price_per_person=price_per_person,
            currency=offers_dict.get("priceCurrency", "PLN") if isinstance(offers_dict, dict) else "PLN",
            offer_url=offer_url,
            image_url=image_url,
        )

