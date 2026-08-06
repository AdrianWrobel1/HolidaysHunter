import base64
import json
import logging
import re
from typing import Any

import httpx

try:
    from playwright.async_api import async_playwright
except ImportError:
    async_playwright = None  # type: ignore[assignment]

from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)

TUI_BASE_SEARCH_URL = "https://www.tui.pl/wypoczynek/wyniki-wyszukiwania-samolot"

COUNTRY_CODE_MAP: dict[str, str] = {
    "Hiszpania": "ESP",
    "Grecja": "GRE",
    "Turcja": "TUR",
    "Egipt": "EGY",
    "Włochy": "ITA",
    "Bułgaria": "BGR",
    "Cypr": "CYP",
    "Chorwacja": "HRV",
    "Tunezja": "TUN",
    "Dominikana": "DOM",
    "Malediwy": "MDV",
    "Meksyk": "MEX",
    "Zjednoczone Emiraty Arabskie": "ARE",
    "Tanzania": "TZA",
    "Albania": "ALB",
    "Czarnogóra": "MNE",
    "Portugalia": "PRT",
}


def decode_next_data_payload(html: str) -> dict[str, Any]:
    """Extract and decode __NEXT_DATA__ payload automatically (handles raw JSON and Base64)."""
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.DOTALL)
    if not match:
        raise ValueError("Script tag <script id=\"__NEXT_DATA__\"> was not found in HTML response.")

    raw_content = match.group(1).strip()
    if not raw_content:
        raise ValueError("__NEXT_DATA__ script tag content is empty.")

    # 1. Check if raw_content is plain JSON
    if raw_content.startswith("{") or raw_content.startswith("["):
        try:
            return json.loads(raw_content)
        except Exception as err:
            raise ValueError(f"Failed to parse plain JSON __NEXT_DATA__: {err}") from err

    # 2. Attempt Base64 decoding
    try:
        decoded_bytes = base64.b64decode(raw_content)
        decoded_str = decoded_bytes.decode("utf-8")
        return json.loads(decoded_str)
    except Exception as err:
        raise ValueError(f"Failed to Base64 decode __NEXT_DATA__ content: {err}") from err


def score_offer_item(item: Any) -> int:
    """Check if an item is a valid offer dictionary and score its quality/completeness."""
    if not isinstance(item, dict):
        return 0

    score = 0
    # Mandatory offer code / ID
    if item.get("offerCode") or item.get("hotelCode") or item.get("id"):
        score += 1
    else:
        return 0

    # Mandatory hotel name / title
    if item.get("hotelName") or item.get("name") or item.get("title"):
        score += 1
    else:
        return 0

    # Mandatory price field
    price = (
        item.get("discountPerPersonPrice")
        or item.get("originalPerPersonPrice")
        or item.get("pricePerAdult")
        or item.get("totalPrice")
        or item.get("discountFullPrice")
    )
    if price is not None:
        score += 1
    else:
        return 0

    # Mandatory date
    if item.get("departureDate") or item.get("departureFlight"):
        score += 1
    else:
        return 0

    # Optional quality fields
    if item.get("returnDate") or item.get("returnFlight"):
        score += 1
    if item.get("boardType") or item.get("boardCode") or item.get("boardName"):
        score += 1
    if item.get("departureAirport"):
        score += 1

    return score


def discover_best_offer_collection(next_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Automatically discover all candidate offer collections in pageProps and rank them by data quality/completeness."""
    page_props = next_data.get("props", {}).get("pageProps", {})
    if not page_props:
        # Fallback to root object if pageProps is not nested
        page_props = next_data

    candidates: list[tuple[int, int, str, list[dict[str, Any]]]] = []

    for key, value in page_props.items():
        offer_list: list[dict[str, Any]] = []

        if isinstance(value, list) and len(value) > 0:
            if isinstance(value[0], dict) and "offers" in value[0] and isinstance(value[0]["offers"], list):
                offer_list = value[0]["offers"]
            elif all(isinstance(x, dict) for x in value):
                offer_list = value  # type: ignore[assignment]
        elif isinstance(value, dict) and "offers" in value and isinstance(value["offers"], list):
            offer_list = value["offers"]

        if not offer_list:
            continue

        valid_count = 0
        total_quality = 0
        for item in offer_list:
            item_score = score_offer_item(item)
            if item_score >= 4:  # Contains mandatory fields (id, name, price, date)
                valid_count += 1
                total_quality += item_score

        if valid_count > 0:
            candidates.append((valid_count, total_quality, key, offer_list))

    if not candidates:
        raise ValueError(
            f"No valid offer collection matching NormalizedOffer requirements found in pageProps keys: {list(page_props.keys())}"
        )

    # Sort candidates by count of valid offers desc, then by total quality score desc
    candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
    best = candidates[0]
    logger.info(
        "TUI: Discovered best offer collection under pageProps key '%s' with %d valid offers (quality score %d).",
        best[2],
        best[0],
        best[1],
    )
    return best[3]


class TuiProvider(BaseProvider):
    """Imports offers from TUI by fetching search page state and extracting __NEXT_DATA__."""

    async def fetch_offers(self, filter_params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        from app.core.countries import get_country_slug, normalize_country_name

        country_param = filter_params.get("country") if filter_params else None
        target_country = "Hiszpania"
        if isinstance(country_param, list) and country_param:
            target_country = country_param[0]
        elif isinstance(country_param, str) and country_param:
            target_country = country_param

        canonical_country = normalize_country_name(target_country)
        country_code = COUNTRY_CODE_MAP.get(canonical_country)

        if country_code:
            target_url = f"{TUI_BASE_SEARCH_URL}?pm_source=OFFERS&pm_name=Search_Form&destinationsCodes={country_code}"
        else:
            slug = get_country_slug(target_country)
            target_url = f"https://www.tui.pl/wypoczynek/{slug}"

        logger.info("TUI: fetching offers from %s (filters=%s)", target_url, filter_params)

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        # Step 1: Try fast HTTP GET via httpx
        httpx_failure_reason: str | None = None
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=headers) as client:
                resp = await client.get(target_url)

            if resp.status_code != 200:
                httpx_failure_reason = f"HTTP GET returned status code {resp.status_code}"
            else:
                next_data = decode_next_data_payload(resp.text)
                offers = discover_best_offer_collection(next_data)
                logger.info("TUI: successfully extracted %d offer objects via httpx.", len(offers))
                return offers

        except Exception as exc:
            httpx_failure_reason = str(exc)

        # Log explicit error before falling back to Playwright
        logger.error(
            "TUI: HTTP GET parser failed before Playwright fallback for URL %s. Reason: %s",
            target_url,
            httpx_failure_reason,
        )

        # Step 2: Fallback to Playwright headless browser
        if async_playwright is None:
            logger.error("TUI: Playwright is not installed; cannot proceed with fallback.")
            return []

        try:
            logger.info("TUI: attempting Playwright fallback for %s", target_url)
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
                )
                page = await browser.new_page(
                    user_agent=headers["User-Agent"],
                    viewport={"width": 1920, "height": 1080},
                )
                await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)
                html = await page.content()
                await browser.close()

            next_data = decode_next_data_payload(html)
            offers = discover_best_offer_collection(next_data)
            logger.info("TUI: successfully extracted %d offer objects via Playwright fallback.", len(offers))
            return offers
        except Exception as exc:
            logger.error("TUI: Playwright fallback also failed for %s: %s", target_url, exc)
            return []
