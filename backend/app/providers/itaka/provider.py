import json
import logging
import re
from typing import Any

import httpx
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)

ITAKA_PAGE_URL = "https://www.itaka.pl/wyniki-wyszukiwania/wakacje/egipt/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
}


class ItakaProvider(BaseProvider):
    """Imports offers from ITAKA by fetching search HTML and extracting __NEXT_DATA__."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=HEADERS,
        )

    def _extract_offers_from_html(self, html: str) -> list[dict[str, Any]]:
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
        if not match:
            return []

        try:
            next_data = json.loads(match.group(1))
            initial_qs = next_data.get("props", {}).get("pageProps", {}).get("initialQueryState", {})
            queries = initial_qs.get("queries", [])

            for q in queries:
                state_data = q.get("state", {}).get("data")
                if isinstance(state_data, dict):
                    main = state_data.get("main", {})
                    if isinstance(main, dict):
                        rates = main.get("rates", {})
                        if isinstance(rates, dict):
                            offer_list = rates.get("list", [])
                            if offer_list:
                                return offer_list
        except Exception as exc:
            logger.error("ITAKA: error parsing JSON: %s", exc)
        return []

    async def fetch_offers(self, filter_params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Fetch raw offer data from ITAKA __NEXT_DATA__."""
        from app.core.countries import get_country_slug

        country_param = filter_params.get("country") if filter_params else None
        target_slug = "hiszpania"
        if isinstance(country_param, list) and country_param:
            target_slug = get_country_slug(country_param[0])
        elif isinstance(country_param, str) and country_param:
            target_slug = get_country_slug(country_param)

        candidate_urls = [
            f"https://www.itaka.pl/wyniki-wyszukiwania/wakacje/{target_slug}/?order=popularity",
            f"https://www.itaka.pl/wyniki-wyszukiwania/wczasy/{target_slug}/?order=popularity",
            f"https://www.itaka.pl/wyniki-wyszukiwania/wakacje/{target_slug}/",
            f"https://www.itaka.pl/wyniki-wyszukiwania/wczasy/{target_slug}/",
        ]

        for target_url in candidate_urls:
            logger.info("ITAKA: trying candidate URL %s (filters=%s)", target_url, filter_params)
            try:
                response = await self._client.get(target_url)
                response.raise_for_status()
                offers = self._extract_offers_from_html(response.text)
                if offers:
                    logger.info("ITAKA: successfully extracted %d offers from __NEXT_DATA__ via %s", len(offers), target_url)
                    return offers
            except Exception as exc:
                logger.warning("ITAKA: httpx request failed for %s (%s)", target_url, exc)

        # Fallback to Playwright if httpx returns 0 offers across candidates
        primary_url = candidate_urls[0]
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                page = await browser.new_page(user_agent=HEADERS["User-Agent"])
                await page.goto(primary_url, wait_until="networkidle", timeout=30000)
                html = await page.content()
                await browser.close()

            offers = self._extract_offers_from_html(html)
            logger.info("ITAKA: extracted %d offers via Playwright fallback.", len(offers))
            return offers
        except Exception as exc:
            logger.error("ITAKA: Playwright fallback failed: %s", exc)
            return []

    async def close(self) -> None:
        await self._client.aclose()
