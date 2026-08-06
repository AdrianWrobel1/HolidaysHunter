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

    @staticmethod
    def _is_valid_offer_item(item: Any) -> bool:
        if not isinstance(item, dict):
            return False
        keys = set(item.keys())
        signatures = {"supplierObjectId", "participantGroups", "rateId", "hotel", "segments", "offerId", "supplier"}
        return len(keys.intersection(signatures)) >= 1

    def _discover_offer_list(self, next_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Resiliently discover offer collections in __NEXT_DATA__ by inspecting query states and pageProps."""
        page_props = next_data.get("props", {}).get("pageProps", {})
        initial_qs = page_props.get("initialQueryState", {})
        queries = initial_qs.get("queries", []) if isinstance(initial_qs, dict) else []

        # 1. Search queries in initialQueryState
        for idx, q in enumerate(queries):
            if not isinstance(q, dict):
                continue
            state_data = q.get("state", {}).get("data")
            if not isinstance(state_data, dict):
                continue

            for section_key, section_val in state_data.items():
                if not isinstance(section_val, dict):
                    continue

                # Look for rate collections (rates, multiRoomRates, etc.) or lists of offer dicts
                for key, val in section_val.items():
                    if isinstance(val, dict):
                        candidate_list = val.get("list")
                        if isinstance(candidate_list, list) and candidate_list:
                            if self._is_valid_offer_item(candidate_list[0]):
                                logger.info(
                                    "ITAKA: resilient discovery found %d offers in query[%d].state.data.%s.%s.list",
                                    len(candidate_list), idx, section_key, key,
                                )
                                return candidate_list
                    elif isinstance(val, list) and val:
                        if self._is_valid_offer_item(val[0]):
                            logger.info(
                                "ITAKA: resilient discovery found %d offers in query[%d].state.data.%s.%s",
                                len(val), idx, section_key, key,
                            )
                            return val

        # 2. Recursive fallback search across pageProps if state query structure changes
        def _recursive_search_offers(obj: Any, depth: int = 0) -> list[dict[str, Any]] | None:
            if depth > 6:
                return None
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k == "list" and isinstance(v, list) and v and self._is_valid_offer_item(v[0]):
                        return v
                    res = _recursive_search_offers(v, depth + 1)
                    if res:
                        return res
            elif isinstance(obj, list):
                for elem in obj:
                    res = _recursive_search_offers(elem, depth + 1)
                    if res:
                        return res
            return None

        fallback_list = _recursive_search_offers(page_props)
        if fallback_list:
            logger.info("ITAKA: resilient discovery found %d offers via recursive pageProps fallback", len(fallback_list))
            return fallback_list

        # 3. If no supported offer collection is found, fail loudly with diagnostics
        available_page_props_keys = list(page_props.keys()) if isinstance(page_props, dict) else type(page_props)
        available_queries = [
            {"queryKey": q.get("queryKey"), "data_keys": list(q.get("state", {}).get("data", {}).keys()) if isinstance(q.get("state", {}).get("data"), dict) else None}
            for q in queries if isinstance(q, dict)
        ]
        logger.error(
            "ITAKA: Failed to discover offer dataset in __NEXT_DATA__! pageProps_keys=%s, queries=%s",
            available_page_props_keys, available_queries,
        )
        raise RuntimeError(
            f"ITAKA: Failed to discover offer dataset in __NEXT_DATA__. "
            f"PageProps keys: {available_page_props_keys}, Query count: {len(queries)}"
        )

    def _extract_offers_from_html(self, html: str) -> list[dict[str, Any]]:
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
        if not match:
            logger.error("ITAKA: __NEXT_DATA__ script tag not found in HTML response.")
            raise RuntimeError("ITAKA: __NEXT_DATA__ script tag missing from response HTML.")

        try:
            next_data = json.loads(match.group(1))
            return self._discover_offer_list(next_data)
        except RuntimeError:
            raise
        except Exception as exc:
            logger.error("ITAKA: error parsing __NEXT_DATA__ JSON: %s", exc)
            raise RuntimeError(f"ITAKA: Invalid __NEXT_DATA__ JSON structure: {exc}") from exc

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
