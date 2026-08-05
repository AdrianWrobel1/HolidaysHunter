import logging
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from app.core.countries import normalize_country_name
from app.models.enums import MealType, Provider, TransportType
from app.providers.base import BaseNormalizer
from app.providers.schemas import NormalizedOffer, build_direct_offer_url

logger = logging.getLogger(__name__)

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
    val_str = str(value).strip()
    # Check for DD.MM.YYYY
    if "." in val_str and len(val_str) >= 10:
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


def _resolve_meal_type(raw: str | None) -> MealType:
    if not raw:
        return MealType.SELF_CATERING
    cleaned = raw.lower().strip()
    try:
        return MealType(cleaned)
    except ValueError:
        pass
    return MEAL_TYPE_MAP.get(cleaned, MealType.SELF_CATERING)


class TuiNormalizer(BaseNormalizer):
    """Maps TUI raw __NEXT_DATA__ JSON offer to NormalizedOffer schema."""

    def normalize(self, raw_offer: dict[str, Any]) -> NormalizedOffer | None:
        offer_id = raw_offer.get("offerCode") or raw_offer.get("hotelCode") or raw_offer.get("id")
        if not offer_id:
            logger.warning("TUI: skipping offer without ID")
            return None

        price_per_person = _parse_decimal(
            raw_offer.get("discountPerPersonPrice") or raw_offer.get("originalPerPersonPrice") or raw_offer.get("pricePerAdult")
        )
        price_total = _parse_decimal(
            raw_offer.get("discountFullPrice") or raw_offer.get("originalFullPrice") or raw_offer.get("totalPrice")
        )

        adults = 2
        children = 0
        participants_str = raw_offer.get("participants", "")
        if "Dorosłych" in participants_str:
            try:
                adults = int(participants_str.split("Dorosłych")[0].strip())
            except Exception:
                pass

        if price_per_person is None and price_total is not None and adults > 0:
            price_per_person = (price_total / adults).quantize(Decimal("0.01"))
        elif price_total is None and price_per_person is not None:
            price_total = price_per_person * adults

        if price_per_person is None or price_total is None or price_total <= 0 or price_per_person <= 0:
            logger.warning("TUI: skipping offer %s — invalid price", offer_id)
            return None

        departure_date = _parse_date(raw_offer.get("departureDate"))
        return_date = _parse_date(raw_offer.get("returnDate"))
        duration = int(raw_offer.get("duration", 7))

        if departure_date is None:
            logger.warning("TUI: skipping offer %s — missing departure date", offer_id)
            return None

        if return_date is None:
            return_date = departure_date + timedelta(days=duration)

        hotel_name = raw_offer.get("hotelName") or raw_offer.get("name", "Unknown Hotel")

        hotel_stars: float | None = None
        stars_raw = raw_offer.get("hotelStandard") or raw_offer.get("hotelStars") or raw_offer.get("category")
        if stars_raw is not None:
            try:
                hotel_stars = float(stars_raw)
            except (ValueError, TypeError):
                pass

        hotel_rating: float | None = None
        rating_raw = raw_offer.get("tripAdvisorRating") or raw_offer.get("hotelRating") or raw_offer.get("score")
        if rating_raw is not None:
            try:
                hotel_rating = float(rating_raw)
            except (ValueError, TypeError):
                pass

        breadcrumbs = raw_offer.get("breadcrumbs", [])
        raw_country = breadcrumbs[0].get("label") if len(breadcrumbs) > 0 else (raw_offer.get("countryName") or raw_offer.get("country") or "Hiszpania")
        country = normalize_country_name(raw_country)
        raw_region = breadcrumbs[1].get("label") if len(breadcrumbs) > 1 else raw_offer.get("regionName")
        region = raw_region if raw_region and raw_region.lower() != country.lower() else None
        city = raw_offer.get("cityName") or raw_offer.get("city")

        raw_url = raw_offer.get("offerUrl") or raw_offer.get("url") or raw_offer.get("detailUrl")
        offer_url = build_direct_offer_url(Provider.TUI, str(offer_id), raw_url)

        image_url = raw_offer.get("imageUrl") or raw_offer.get("pictureUrl") or (raw_offer.get("gallery", [{}])[0].get("url") if raw_offer.get("gallery") else None)

        dur_val = raw_offer.get("durationNights") or raw_offer.get("duration", 7)
        duration = int(dur_val)

        adults = raw_offer.get("adultCount") or adults
        children = raw_offer.get("childCount") or children

        return NormalizedOffer(
            external_id=str(offer_id),
            provider=Provider.TUI,
            title=hotel_name,
            country=country,
            region=region,
            city=city,
            hotel_name=hotel_name,
            hotel_stars=hotel_stars,
            hotel_rating=hotel_rating,
            departure_date=departure_date,
            return_date=return_date,
            duration_nights=duration,
            departure_city=raw_offer.get("departureAirport", "Warszawa"),
            adults=adults,
            children=children,
            meal_type=_resolve_meal_type(raw_offer.get("boardType") or raw_offer.get("boardCode") or raw_offer.get("boardName")),
            transport_type=TransportType.FLIGHT,
            price_total=price_total,
            price_per_person=price_per_person,
            currency="PLN",
            offer_url=offer_url,
            image_url=image_url,
        )
