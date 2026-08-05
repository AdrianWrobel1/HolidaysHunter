import logging
import re
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
    try:
        return date.fromisoformat(str(value)[:10])
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


TRANSPORT_TYPE_MAP: dict[str, TransportType] = {
    "samolot": TransportType.FLIGHT,
    "flight": TransportType.FLIGHT,
    "autokar": TransportType.BUS,
    "bus": TransportType.BUS,
    "dojazd własny": TransportType.OWN,
    "dojazd wlasny": TransportType.OWN,
    "own": TransportType.OWN,
}


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text).strip('-')
    return text


def _resolve_transport_type(raw: str | None) -> TransportType:
    if not raw:
        return TransportType.FLIGHT
    cleaned = raw.lower().strip()
    return TRANSPORT_TYPE_MAP.get(cleaned, TransportType.FLIGHT)


class ItakaNormalizer(BaseNormalizer):
    """Maps ITAKA raw __NEXT_DATA__ JSON offer to NormalizedOffer schema."""

    def normalize(self, raw_offer: dict[str, Any]) -> NormalizedOffer | None:
        offer_id = raw_offer.get("id") or raw_offer.get("offerId") or raw_offer.get("supplierObjectId")
        supplier_obj_id = raw_offer.get("supplierObjectId", "")
        if not offer_id:
            logger.warning("ITAKA [normalizer]: skipping offer without ID")
            return None

        raw_price = raw_offer.get("price") or raw_offer.get("priceTotal")
        if raw_price is None:
            logger.warning("ITAKA [normalizer]: skipping offer %s — missing price", offer_id)
            return None

        parsed_price = _parse_decimal(raw_price)
        if parsed_price is None or parsed_price <= 0:
            logger.warning("ITAKA [normalizer]: skipping offer %s — invalid price", offer_id)
            return None

        # React Query state uses grosze (e.g. 599800 grosze -> 5998.00 PLN)
        if parsed_price >= Decimal("100000"):
            price_total = (parsed_price / Decimal("100")).quantize(Decimal("0.01"))
        else:
            price_total = parsed_price.quantize(Decimal("0.01"))

        participants = raw_offer.get("participants", [])
        adults = raw_offer.get("adults") or len([p for p in participants if p.get("type") == "adult"]) or 2
        children = raw_offer.get("children") or len([p for p in participants if p.get("type") == "child"]) or 0

        raw_ppp = raw_offer.get("pricePerPerson")
        price_per_person: Decimal | None = None
        if raw_ppp is not None:
            parsed_ppp = _parse_decimal(raw_ppp)
            if parsed_ppp:
                price_per_person = (parsed_ppp / Decimal("100")).quantize(Decimal("0.01")) if parsed_ppp >= Decimal("100000") else parsed_ppp.quantize(Decimal("0.01"))
        elif participants and participants[0].get("price"):
            p_val = _parse_decimal(participants[0].get("price"))
            if p_val:
                price_per_person = (p_val / Decimal("100")).quantize(Decimal("0.01")) if p_val >= Decimal("100000") else p_val.quantize(Decimal("0.01"))
        elif (adults + children) > 0:
            price_per_person = (price_total / (adults + children)).quantize(Decimal("0.01"))

        if price_per_person is None:
            logger.warning("ITAKA: skipping offer %s — cannot determine per-person price", offer_id)
            return None

        segments = raw_offer.get("segments", [])
        flight_seg = next((s for s in segments if isinstance(s, dict) and s.get("type") == "flight"), {})
        hotel_seg = next((s for s in segments if isinstance(s, dict) and s.get("type") == "hotel"), {})

        departure_date = _parse_date(hotel_seg.get("beginDate") or flight_seg.get("beginDateTime") or raw_offer.get("departureDate") or raw_offer.get("dateFrom"))
        return_date = _parse_date(hotel_seg.get("endDate") or flight_seg.get("endDateTime") or raw_offer.get("returnDate") or raw_offer.get("dateTo"))

        dur_val = raw_offer.get("duration") or raw_offer.get("nights")
        if isinstance(dur_val, int):
            duration = dur_val
        elif isinstance(dur_val, dict):
            duration = dur_val.get("days", 7)
        else:
            duration = 7

        if departure_date is None:
            logger.warning("ITAKA: skipping offer %s — missing departure date", offer_id)
            return None

        if return_date is None:
            return_date = departure_date + timedelta(days=duration)

        content = hotel_seg.get("content", {}) if isinstance(hotel_seg, dict) else {}
        hotel_obj = raw_offer.get("hotel") if isinstance(raw_offer.get("hotel"), dict) else {}
        hotel_name = content.get("title") or raw_offer.get("hotelName") or hotel_obj.get("name") or raw_offer.get("title", "Unknown Hotel")

        hotel_rating_raw = content.get("hotelRating") or raw_offer.get("hotelRating") or hotel_obj.get("rating")
        hotel_rating: float | None = float(hotel_rating_raw) if hotel_rating_raw is not None else None

        hotel_stars_raw = raw_offer.get("hotelStars") or hotel_obj.get("stars")
        hotel_stars: float | None = float(hotel_stars_raw) if hotel_stars_raw is not None else None
        if hotel_stars is None and hotel_rating_raw is not None:
            try:
                val = float(hotel_rating_raw)
                hotel_stars = val / 10.0 if val > 10 else val
            except (ValueError, TypeError):
                pass

        geo_ids = content.get("geographicalIdentifiers", []) if isinstance(content, dict) else []
        cntry_item = next((item for item in geo_ids if isinstance(item, dict) and item.get("type") == "country"), {})
        rgn_item = next((item for item in geo_ids if isinstance(item, dict) and item.get("type") in ("province", "region")), {})

        # --- Country resolution (priority: geographicalIdentifiers[country] > raw_offer.country > fallback) ---
        # NOTE: flight_seg.destination is NOT used as a country source because it often contains
        # city names (e.g. "Malaga") not country names. It is used for region resolution instead.
        raw_country_from_geo = cntry_item.get("title") if cntry_item else None
        raw_country_from_offer = raw_offer.get("country")
        raw_country = raw_country_from_geo or raw_country_from_offer

        canonical_country = normalize_country_name(raw_country) if raw_country else "Inne"

        # If the "country" resolved from geo/offer data is not a real country (e.g. "Malaga"),
        # normalize_country_name will map it via COUNTRY_CANONICAL_MAP (e.g. malaga -> Hiszpania).
        # Log a diagnostic message when the raw value differs from the canonical one.
        if raw_country and canonical_country.lower() != (raw_country or "").lower():
            logger.debug(
                "ITAKA [normalizer]: offer %s — raw_country=%r normalized to canonical=%r",
                offer_id, raw_country, canonical_country,
            )

        raw_region = rgn_item.get("title") if rgn_item else None
        if not raw_region:
            raw_region = raw_offer.get("region")
        # Use flight destination as region fallback only (not as country)
        if not raw_region and isinstance(flight_seg, dict):
            dest_title = flight_seg.get("destination", {}).get("title")
            if dest_title and dest_title.lower() != canonical_country.lower():
                raw_region = dest_title
                logger.debug(
                    "ITAKA [normalizer]: offer %s — using flight destination %r as region",
                    offer_id, dest_title,
                )

        region_title = raw_region if raw_region and raw_region.lower() != canonical_country.lower() else None

        logger.debug(
            "ITAKA [normalizer]: offer %s — country=%r region=%r (geo_ids=%d entries)",
            offer_id, canonical_country, region_title, len(geo_ids),
        )

        departure_city = (flight_seg.get("departure", {}).get("title") if isinstance(flight_seg, dict) else None) or raw_offer.get("departureCity") or raw_offer.get("departureFrom") or "Warszawa"

        meal_title = (hotel_seg.get("meal", {}).get("title") if isinstance(hotel_seg, dict) else None) or raw_offer.get("boardType") or raw_offer.get("mealType")
        transport_title = (flight_seg.get("type") if isinstance(flight_seg, dict) else None) or raw_offer.get("transportType") or raw_offer.get("transport")

        hotel_slug = _slugify(hotel_name)
        raw_url = raw_offer.get("url") or raw_offer.get("offerUrl") or raw_offer.get("webUrl")
        relative_url = raw_url or (f"/wczasy/{canonical_country.lower()}/{hotel_slug},{supplier_obj_id}/?id={offer_id}" if supplier_obj_id else None)

        from app.providers.schemas import build_direct_offer_url
        offer_url = build_direct_offer_url(Provider.ITAKA, str(offer_id), relative_url)

        photos = content.get("photos", {}).get("gallery", []) if isinstance(content, dict) and isinstance(content.get("photos"), dict) else []
        image_url = raw_offer.get("imageUrl") or (photos[0] if photos else None)

        return NormalizedOffer(
            external_id=str(offer_id),
            provider=Provider.ITAKA,
            title=hotel_name,
            country=canonical_country,
            region=region_title,
            city=raw_offer.get("city"),
            hotel_name=hotel_name,
            hotel_stars=hotel_stars,
            hotel_rating=hotel_rating,
            departure_date=departure_date,
            return_date=return_date,
            duration_nights=duration,
            departure_city=departure_city,
            adults=adults,
            children=children,
            meal_type=_resolve_meal_type(meal_title),
            transport_type=_resolve_transport_type(transport_title),
            price_total=price_total,
            price_per_person=price_per_person,
            currency="PLN",
            offer_url=offer_url,
            image_url=image_url,
        )
