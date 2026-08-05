import logging
import re
from typing import Any

import httpx

from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)

WAKACJE_PL_PAGE_URL = "https://www.wakacje.pl/wczasy/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/121.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
}


class WakacjePlProvider(BaseProvider):
    """Imports offers from Wakacje.pl by fetching HTML and extracting rendered offer cards & hrefs."""

    def __init__(self) -> None:
        self._client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers=HEADERS,
        )

    async def fetch_offers(self, filter_params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Fetch raw offer data from Wakacje.pl HTML."""
        from app.core.countries import get_country_slug

        country_param = filter_params.get("country") if filter_params else None
        target_slug = "hiszpania"
        if isinstance(country_param, list) and country_param:
            target_slug = get_country_slug(country_param[0])
        elif isinstance(country_param, str) and country_param:
            target_slug = get_country_slug(country_param)

        target_url = f"https://www.wakacje.pl/wczasy/{target_slug}/"
        try:
            logger.info("Wakacje.pl: fetching HTML from %s (filters=%s)", target_url, filter_params)
            response = await self._client.get(target_url)
            response.raise_for_status()
            html = response.text
        except Exception as exc:
            logger.error("Wakacje.pl: HTTP request failed for %s: %s", target_url, exc)
            return []

        # Match all offer card hrefs and surrounding link tags
        # Pattern: <a href="https://www.wakacje.pl/oferty/...">
        card_matches = re.findall(r'<a[^>]*href=["\'](https://www\.wakacje\.pl/oferty/[^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL)

        raw_offers: list[dict[str, Any]] = []
        seen_urls = set()

        for href, inner_html in card_matches:
            if href in seen_urls:
                continue
            seen_urls.add(href)
            
            # Clean HTML tags to text
            text_content = re.sub(r'<[^>]+>', ' ', inner_html).strip()
            raw_offers.append({
                "href": href,
                "text": text_content,
                "inner_html": inner_html[:1000]
            })

        # If regex didn't catch cards (e.g. if SSR cards use relative hrefs), also search relative
        if not raw_offers:
            rel_matches = re.findall(r'<a[^>]*href=["\'](/oferty/[^"\']+)["\'][^>]*>(.*?)</a>', html, re.DOTALL)
            for href, inner_html in rel_matches:
                full_href = f"https://www.wakacje.pl{href}"
                if full_href in seen_urls:
                    continue
                seen_urls.add(full_href)
                text_content = re.sub(r'<[^>]+>', ' ', inner_html).strip()
                raw_offers.append({
                    "href": full_href,
                    "text": text_content,
                    "inner_html": inner_html[:1000]
                })

        logger.info("Wakacje.pl: successfully extracted %d offer cards from HTML.", len(raw_offers))
        return raw_offers

    async def close(self) -> None:
        await self._client.aclose()
