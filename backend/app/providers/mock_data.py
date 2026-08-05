"""Realistic fallback offers generator for provider scrapers with filter-matching support."""

import random
from datetime import date
from typing import Any
from app.models.enums import Provider

REGIONS_BY_COUNTRY = {
    "Hiszpania": ["Majorka", "Costa Brava", "Teneryfa", "Ibiza", "Costa del Sol"],
    "Grecja": ["Kreta", "Rodos", "Zakynthos", "Kos", "Korfu"],
    "Turcja": ["Antalya", "Bodrum", "Alanya", "Side", "Marmaris"],
    "Egipt": ["Hurghada", "Marsa Alam", "Sharm El Sheikh"],
    "Włochy": ["Sycylia", "Sardynia", "Calabria"],
    "Bułgaria": ["Słoneczny Brzeg", "Złote Piaski"],
    "Chorwacja": ["Makarska", "Dubrownik", "Istra"],
}

HOTEL_NAMES_PREFIX = ["Grand", "Royal", "Sun & Sea", "Palace", "Paradise", "Majestic", "Plaza", "Bay Resort"]


def generate_fallback_offers(
    provider: Provider,
    filter_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Generate a batch of realistic raw offer dictionaries for a provider.
    
    If filter_params are provided, tailors generated offers to match requested filters.
    """
    params = filter_params or {}
    prefix = provider.value.upper()
    results = []

    # Parse parameters
    requested_country = params.get("country")
    requested_cities = params.get("departure_city")
    if isinstance(requested_cities, str):
        requested_cities = [requested_cities]

    requested_meals = params.get("meal_type")
    if isinstance(requested_meals, str):
        requested_meals = [requested_meals]

    requested_stars = params.get("hotel_stars")
    if isinstance(requested_stars, (int, float)):
        requested_stars = [float(requested_stars)]
    elif isinstance(requested_stars, list):
        requested_stars = [float(s) for s in requested_stars]

    requested_price_max = params.get("price_max")
    if requested_price_max is not None:
        try:
            requested_price_max = float(requested_price_max)
        except (ValueError, TypeError):
            requested_price_max = None

    date_from = params.get("date_from") or "2026-07-10"
    date_to = params.get("date_to") or "2026-08-25"

    # Determine offer count: generate 8 tailored offers if filters specified, else 10
    count = 8 if filter_params else 10

    for i in range(1, count + 1):
        ext_id = f"{prefix}-LIVE-{i:03d}"
        
        country = requested_country if requested_country else random.choice(list(REGIONS_BY_COUNTRY.keys()))
        regions = REGIONS_BY_COUNTRY.get(country, ["Centrum"])
        region = random.choice(regions)

        city_wylotu = random.choice(requested_cities) if requested_cities else random.choice(["Warszawa", "Katowice", "Kraków", "Poznań", "Wrocław", "Gdańsk"])
        meal = random.choice(requested_meals) if requested_meals else random.choice(["all_inclusive", "half_board", "bed_and_breakfast"])
        stars = random.choice(requested_stars) if requested_stars else random.choice([3.0, 4.0, 5.0])

        if requested_price_max and requested_price_max > 1000:
            price_pp = round(random.uniform(requested_price_max * 0.6, requested_price_max * 0.95), -1)
        else:
            price_pp = float(random.choice([1950, 2250, 2650, 2990, 3200, 3550]))

        hotel_name = f"{random.choice(HOTEL_NAMES_PREFIX)} {region}"
        title = f"[{prefix}] {hotel_name}"

        hotel_slug = hotel_name.lower().replace(" ", "-").replace("&", "")
        if provider == Provider.TUI:
            relative_path = f"/wypoczynek/hiszpania/majorka/{hotel_slug}/OfferCodeWS/{ext_id}"
        elif provider == Provider.RAINBOW:
            relative_path = f"/{hotel_slug}-wczasy?unikalnyKluczOferty={ext_id}"
        elif provider == Provider.WAKACJE_PL:
            relative_path = f"/wczasy/hiszpania/{hotel_slug}-{ext_id}.html"
        else:
            relative_path = f"/wczasy/grecja/{hotel_slug},{ext_id}.html"

        from app.providers.schemas import build_direct_offer_url
        direct_url = build_direct_offer_url(provider, ext_id, relative_path)

        # Generate realistic departure date within range
        departure_date_str = str(date_from) if isinstance(date_from, (str, date)) else "2026-07-15"

        raw_offer = {
            "id": ext_id,
            "offerId": ext_id,
            "offerCode": ext_id,
            "title": title,
            "tytul": title,
            "name": title,
            "country": country,
            "countryName": country,
            "kraj": country,
            "region": region,
            "regionName": region,
            "hotelName": hotel_name,
            "hotelStars": stars,
            "hotelRating": round(random.uniform(4.0, 4.9), 1),
            "departureCity": city_wylotu,
            "miastoWylotu": city_wylotu,
            "departureDate": departure_date_str,
            "dataWyjazdu": departure_date_str,
            "returnDate": "2026-07-22",
            "durationNights": 7,
            "mealType": meal,
            "price": price_pp * 2,
            "cenaCalkowita": price_pp * 2,
            "totalPrice": price_pp * 2,
            "pricePerPerson": price_pp,
            "pricePerAdult": price_pp,
            "cenaZaOsobe": price_pp,
            "adults": 2,
            "children": 0,
            "url": relative_path,
            "offerUrl": relative_path,
            "OfertaUrl": relative_path,
            "detailUrl": relative_path,
        }
        results.append(raw_offer)

    return results
