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


class RainbowNormalizer(BaseNormalizer):
    """Maps Rainbow application/ld+json Product to NormalizedOffer schema."""

    def normalize(self, raw_offer: dict[str, Any]) -> NormalizedOffer | None:
        raw_url = raw_offer.get("url") or raw_offer.get("OfertaUrl") or raw_offer.get("ofertaUrl") or raw_offer.get("offerUrl")

        # Extract external_id from unikalnyKluczOferty or id
        parsed_url = urlparse(raw_url) if raw_url else urlparse("")
        params = parse_qs(parsed_url.query)
        key_list = params.get("unikalnyKluczOferty", [])
        offer_id = raw_offer.get("id") or (key_list[0] if key_list else None)
        if not offer_id:
            logger.warning("Rainbow: skipping offer without ID")
            return None

        offers_dict = raw_offer.get("offers", {})
        price_raw = (offers_dict.get("price") if isinstance(offers_dict, dict) else None) or raw_offer.get("cenaCalkowita") or raw_offer.get("priceTotal") or raw_offer.get("price")
        price_total = _parse_decimal(price_raw)
        if price_total is None or price_total <= 0:
            logger.warning("Rainbow: skipping offer %s — invalid price", offer_id)
            return None

        adults = raw_offer.get("dorosli") or raw_offer.get("adults") or 2
        children = raw_offer.get("dzieci") or raw_offer.get("children") or 0

        ppp_raw = raw_offer.get("cenaZaOsobe") or raw_offer.get("pricePerPerson")
        price_per_person = _parse_decimal(ppp_raw) if ppp_raw is not None else ((price_total / adults).quantize(Decimal("0.01")) if adults > 0 else price_total)

        name = raw_offer.get("nazwaHotelu") or raw_offer.get("hotelName") or raw_offer.get("tytul") or raw_offer.get("title") or raw_offer.get("name", "Wycieczka Rainbow")
        title = raw_offer.get("tytul") or raw_offer.get("title") or name
        description = raw_offer.get("description", "")

        # Extract country/region from description (e.g. "Objazd • Austria: Wiedeń")
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

        # Dates default to upcoming season if not in URL
        departure_date = _parse_date(raw_offer.get("dataWyjazdu") or raw_offer.get("departureDate"))
        if departure_date is None:
            departure_date = date.today() + timedelta(days=30)
        duration = int(raw_offer.get("liczbaNocy") or raw_offer.get("duration") or 7)
        return_date = _parse_date(raw_offer.get("dataPowrotu") or raw_offer.get("returnDate")) or (departure_date + timedelta(days=duration))

        offer_url = build_direct_offer_url(Provider.RAINBOW, str(offer_id), raw_url)
        image_url = raw_offer.get("zdjecieGlowne") or raw_offer.get("imageUrl") or raw_offer.get("image")

        stars_raw = raw_offer.get("standardHotelu") or raw_offer.get("hotelStars")
        hotel_stars: float | None = float(stars_raw) if stars_raw is not None else None

        rating_raw = raw_offer.get("ocenaHotelu") or raw_offer.get("hotelRating")
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
