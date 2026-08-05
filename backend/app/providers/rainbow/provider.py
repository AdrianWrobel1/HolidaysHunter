import json
import logging
import re
from typing import Any

import httpx

from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)

RAINBOW_PAGE_URL = "https://r.pl/szukaj"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
}


class RainbowProvider(BaseProvider):
    """Imports offers from Rainbow (r.pl) by fetching search HTML and extracting Schema.org ItemList."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=HEADERS,
        )

    async def fetch_offers(self, filter_params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Fetch raw offer data from Rainbow application/ld+json."""
        from app.core.countries import get_country_slug

        country_param = filter_params.get("country") if filter_params else None
        target_slug = "hiszpania"
        if isinstance(country_param, list) and country_param:
            target_slug = get_country_slug(country_param[0])
        elif isinstance(country_param, str) and country_param:
            target_slug = get_country_slug(country_param)

        target_url = f"https://r.pl/{target_slug}"
        try:
            logger.info("Rainbow: fetching HTML from %s (filters=%s)", target_url, filter_params)
            response = await self._client.get(target_url)
            response.raise_for_status()
            html = response.text
        except Exception as exc:
            logger.error("Rainbow: HTTP request failed for %s: %s", target_url, exc)
            return []

        scripts = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html, re.DOTALL)
        raw_offers: list[dict[str, Any]] = []

        for s in scripts:
            try:
                data = json.loads(s.strip())
                if isinstance(data, dict) and data.get("@type") == "ItemList":
                    items = data.get("itemListElement", [])
                    for it in items:
                        prod = it.get("item", {})
                        if isinstance(prod, dict) and prod.get("@type") == "Product":
                            raw_offers.append(prod)
            except Exception:
                continue

        logger.info("Rainbow: successfully extracted %d offers from application/ld+json.", len(raw_offers))
        return raw_offers

    async def close(self) -> None:
        await self._client.aclose()
