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
        # Remove non-digits except dot
        clean = re.sub(r'[^\d.]', '', str(value).replace(',', '.'))
        return Decimal(clean)
    except (InvalidOperation, ValueError, TypeError):
        return None


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    val_str = str(value).strip()
    if "." in val_str:
        parts = val_str[:10].split(".")
        if len(parts) == 3:
            try:
                return date(int(parts[2]), int(parts[1]), int(parts[0]))
            except ValueError:
                pass
    try:
        return date.fromisoformat(val_str[:10])
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
        return MealType.ALL_INCLUSIVE
    cleaned = raw.lower().strip()
    try:
        return MealType(cleaned)
    except ValueError:
        pass
    return MEAL_TYPE_MAP.get(cleaned, MealType.ALL_INCLUSIVE)


class WakacjePlNormalizer(BaseNormalizer):
    """Maps Wakacje.pl HTML offer card data to NormalizedOffer schema."""

    def normalize(self, raw_offer: dict[str, Any]) -> NormalizedOffer | None:
        href = raw_offer.get("href") or raw_offer.get("url") or raw_offer.get("offerUrl") or raw_offer.get("urlName")
        id_match = re.search(r'-(\d+)\.html', href) if href else None
        offer_id = raw_offer.get("id") or (id_match.group(1) if id_match else None)
        if not offer_id:
            logger.warning("Wakacje.pl: skipping offer without ID")
            return None

        # Extract dates from query params or dict
        parsed_url = urlparse(href) if href else urlparse("")
        query = parsed_url.query
        
        departure_date = _parse_date(raw_offer.get("departureDate"))
        dur_val = raw_offer.get("durationNights") or raw_offer.get("duration", 7)
        duration = int(dur_val)
        
        if departure_date is None:
            date_match = re.search(r'od-(\d{4}-\d{2}-\d{2})', query)
            if date_match:
                departure_date = _parse_date(date_match.group(1))
            
        dur_match = re.search(r',(\d+)-dni', query)
        if dur_match:
            duration = int(dur_match.group(1))

        if departure_date is None:
            departure_date = date.today() + timedelta(days=30)

        return_date = _parse_date(raw_offer.get("returnDate")) or (departure_date + timedelta(days=duration))

        # Parse text content from card
        text = raw_offer.get("text", "")
        path_parts = [p for p in parsed_url.path.strip("/").split("/") if p]
        
        if raw_offer.get("country"):
            raw_country = raw_offer["country"]
        elif len(path_parts) > 1 and path_parts[0] == "oferty":
            raw_country = path_parts[1].capitalize()
        elif path_parts:
            raw_country = path_parts[0].capitalize()
        else:
            raw_country = "Turcja"

        country = normalize_country_name(raw_country)

        if raw_offer.get("region"):
            raw_region = raw_offer["region"]
        elif len(path_parts) > 2 and path_parts[0] == "oferty":
            raw_region = path_parts[2].replace("-", " ").capitalize()
        elif len(path_parts) > 1:
            raw_region = path_parts[1].replace("-", " ").capitalize()
        else:
            raw_region = None

        region = raw_region if raw_region and raw_region.lower() != country.lower() else None
        city = raw_offer.get("city") or (path_parts[3].replace("-", " ").capitalize() if len(path_parts) > 3 else None)
        
        hotel_slug = path_parts[-1].replace(".html", "") if path_parts else ""
        hotel_slug = re.sub(r'-\d+$', '', hotel_slug)
        hotel_name = raw_offer.get("hotelName") or raw_offer.get("title") or (hotel_slug.replace("-", " ").title() if hotel_slug else "Unknown Hotel")

        # Search for price in text or query
        price_match = re.search(r'(\d[\d\s]*\d|\d+)\s*zł', text)
        ppp_raw = raw_offer.get("pricePerPerson")
        price_per_person = _parse_decimal(ppp_raw) if ppp_raw is not None else (_parse_decimal(price_match.group(1)) if price_match else Decimal("2500.00"))
        
        pt_raw = raw_offer.get("priceTotal")
        price_total = _parse_decimal(pt_raw) if pt_raw is not None else (price_per_person * 2)

        if price_total is None or price_per_person is None or price_total <= 0 or price_per_person <= 0:
            logger.warning("Wakacje.pl: skipping offer %s — invalid price", offer_id)
            return None

        offer_url = build_direct_offer_url(Provider.WAKACJE_PL, str(offer_id), href)

        title = raw_offer.get("title") or hotel_name

        return NormalizedOffer(
            external_id=str(offer_id),
            provider=Provider.WAKACJE_PL,
            title=title,
            country=country,
            region=region,
            city=city,
            hotel_name=hotel_name,
            hotel_stars=raw_offer.get("hotelStars", 4.5),
            hotel_rating=raw_offer.get("hotelRating"),
            departure_date=departure_date,
            return_date=return_date,
            duration_nights=duration,
            departure_city=raw_offer.get("departureCity", "Katowice"),
            adults=raw_offer.get("adults", 2),
            children=raw_offer.get("children", 0),
            meal_type=_resolve_meal_type(raw_offer.get("mealType") or raw_offer.get("boardType")),
            transport_type=TransportType.FLIGHT,
            price_total=price_total,
            price_per_person=price_per_person,
            currency="PLN",
            offer_url=offer_url,
            image_url=raw_offer.get("imageUrl"),
        )
