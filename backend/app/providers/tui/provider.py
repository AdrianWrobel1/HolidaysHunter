import json
import logging
import re
from typing import Any

from playwright.async_api import async_playwright
from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)

TUI_PAGE_URL = "https://www.tui.pl/wypoczynek/wyniki-wyszukiwania-samolot"


class TuiProvider(BaseProvider):
    """Imports offers from TUI by fetching search HTML via Playwright and extracting __NEXT_DATA__."""

    async def fetch_offers(self, filter_params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Fetch raw offer data from TUI __NEXT_DATA__."""
        from app.core.countries import get_country_slug

        country_param = filter_params.get("country") if filter_params else None
        target_slug = "hiszpania"
        if isinstance(country_param, list) and country_param:
            target_slug = get_country_slug(country_param[0])
        elif isinstance(country_param, str) and country_param:
            target_slug = get_country_slug(country_param)

        target_url = f"https://www.tui.pl/wypoczynek/{target_slug}"
        logger.info("TUI: fetching HTML via Playwright from %s (filters=%s)", target_url, filter_params)
        raw_offers: list[dict[str, Any]] = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
                )
                page = await browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/121.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1920, "height": 1080}
                )
                await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)
                html = await page.content()
                await browser.close()

            match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
            if not match:
                logger.error("TUI: __NEXT_DATA__ script tag not found in HTML response.")
                return []

            next_data = json.loads(match.group(1))
            page_props = next_data.get("props", {}).get("pageProps", {})
            offers_data = page_props.get("initialOffersData")

            if isinstance(offers_data, list) and len(offers_data) > 0:
                if isinstance(offers_data[0], dict) and "offers" in offers_data[0]:
                    raw_offers = offers_data[0].get("offers", [])
                else:
                    raw_offers = offers_data
            elif isinstance(offers_data, dict):
                raw_offers = offers_data.get("offers", [])

            logger.info("TUI: successfully extracted %d offer objects from __NEXT_DATA__.", len(raw_offers))
            return raw_offers
        except Exception as exc:
            logger.error("TUI: failed to fetch/parse __NEXT_DATA__: %s", exc)
            return []
