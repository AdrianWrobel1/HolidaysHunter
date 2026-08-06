"""Diagnostic inspection script for provider import pipelines.

For each provider (ITAKA, TUI, Rainbow, Wakacje.pl):
1. Outgoing request parameters & target URL
2. HTTP status code & response size (bytes)
3. Parsed raw offers count
4. Normalized offers count
5. Saved offers count (and transport filter count)
6. Exact reason if pipeline stops / fails at any step
"""

import asyncio
import json
import logging
import re
import sys
from typing import Any

import httpx

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from app.models.enums import TransportType
from app.providers.itaka.normalizer import ItakaNormalizer
from app.providers.itaka.provider import ItakaProvider
from app.providers.rainbow.normalizer import RainbowNormalizer
from app.providers.rainbow.provider import RainbowProvider
from app.providers.tui.normalizer import TuiNormalizer
from app.providers.tui.provider import TuiProvider
from app.providers.wakacje_pl.normalizer import WakacjePlNormalizer
from app.providers.wakacje_pl.provider import WakacjePlProvider

logging.basicConfig(level=logging.INFO)


async def diagnose_itaka():
    print("\n" + "=" * 80)
    print("DIAGNOSING ITAKA PROVIDER PIPELINE")
    print("=" * 80)

    target_url = "https://www.itaka.pl/wyniki-wyszukiwania/wakacje/hiszpania/?order=popularity"
    print(f"1. Outgoing Request URL / Params: {target_url}")
    print("   Headers: User-Agent, Accept, Accept-Language")

    http_status = None
    response_size = 0
    html_text = ""

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            resp = await client.get(target_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
            })
            http_status = resp.status_code
            response_size = len(resp.content)
            html_text = resp.text
            print(f"2. HTTP Status: {http_status}")
            print(f"3. Response Size: {response_size} bytes ({response_size / 1024:.2f} KB)")
        except Exception as e:
            print(f"2. HTTP Status: ERROR ({e})")
            print("3. Response Size: 0 bytes")

    provider = ItakaProvider()
    normalizer = ItakaNormalizer()

    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_text)
    next_data_found = bool(match)
    print(f"   <script id=\"__NEXT_DATA__\"> found in HTML: {next_data_found}")

    raw_offers = await provider.fetch_offers()
    print(f"4. Parsed Raw Offers Count: {len(raw_offers)}")

    normalized_offers = []
    normalization_failures = []
    for idx, raw in enumerate(raw_offers, 1):
        norm = normalizer.normalize(raw)
        if norm:
            normalized_offers.append(norm)
        else:
            normalization_failures.append((idx, raw))

    print(f"5. Normalized Offers Count: {len(normalized_offers)}")
    if normalization_failures:
        print(f"   (Failed normalizations: {len(normalization_failures)})")

    flight_offers = [o for o in normalized_offers if o.transport_type == TransportType.FLIGHT]
    print(f"   Flight Transport Offers Count: {len(flight_offers)}")
    print(f"6. Saved Offers Count (DB simulation): {len(flight_offers)}")

    reason = None
    if http_status != 200:
        reason = f"Provider API returned HTTP status {http_status}"
    elif not next_data_found:
        reason = "Parser failed: `<script id=\"__NEXT_DATA__\">` tag not present in returned HTML (site structure change or Cloudflare/Bot protection block)"
    elif len(raw_offers) == 0:
        reason = "Parser failed: JSON structure in `__NEXT_DATA__` did not contain expected `props.pageProps.initialQueryState.queries` or rates list"
    elif len(normalized_offers) == 0:
        reason = "Normalization failed: All raw offer objects failed schema validation"
    elif len(flight_offers) == 0:
        reason = "Filters failed: All normalized offers were filtered out by transport type check"

    print(f"7. Pipeline Stop Reason: {reason or 'Pipeline completed successfully'}")


async def diagnose_tui():
    print("\n" + "=" * 80)
    print("DIAGNOSING TUI PROVIDER PIPELINE")
    print("=" * 80)

    target_url = "https://www.tui.pl/wypoczynek/hiszpania"
    print(f"1. Outgoing Request URL / Params: {target_url}")

    http_status = None
    response_size = 0
    html_text = ""

    from playwright.async_api import async_playwright
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080}
            )
            resp = await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(3000)
            if resp:
                http_status = resp.status
            html_text = await page.content()
            response_size = len(html_text.encode('utf-8'))
            await browser.close()
            print(f"2. HTTP Status: {http_status}")
            print(f"3. Response Size: {response_size} bytes ({response_size / 1024:.2f} KB)")
    except Exception as e:
        print(f"2. HTTP Status: ERROR ({e})")
        print("3. Response Size: 0 bytes")

    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html_text)
    next_data_found = bool(match)
    print(f"   <script id=\"__NEXT_DATA__\"> found in HTML: {next_data_found}")

    provider = TuiProvider()
    normalizer = TuiNormalizer()

    raw_offers = await provider.fetch_offers()
    print(f"4. Parsed Raw Offers Count: {len(raw_offers)}")

    normalized_offers = []
    for raw in raw_offers:
        norm = normalizer.normalize(raw)
        if norm:
            normalized_offers.append(norm)

    print(f"5. Normalized Offers Count: {len(normalized_offers)}")
    flight_offers = [o for o in normalized_offers if o.transport_type == TransportType.FLIGHT]
    print(f"6. Saved Offers Count (DB simulation): {len(flight_offers)}")

    reason = None
    if http_status and http_status != 200:
        reason = f"Provider API returned HTTP status {http_status}"
    elif not next_data_found:
        reason = "Parser failed: `<script id=\"__NEXT_DATA__\">` tag not found in TUI rendered HTML"
    elif len(raw_offers) == 0:
        reason = "Parser failed: JSON structure in TUI `__NEXT_DATA__` did not contain `pageProps.initialOffersData` or offers list"
    elif len(normalized_offers) == 0:
        reason = "Normalization failed: All raw offer objects failed schema validation"

    print(f"7. Pipeline Stop Reason: {reason or 'Pipeline completed successfully'}")


async def diagnose_rainbow():
    print("\n" + "=" * 80)
    print("DIAGNOSING RAINBOW PROVIDER PIPELINE")
    print("=" * 80)

    target_url = "https://r.pl/hiszpania"
    print(f"1. Outgoing Request URL / Params: {target_url}")

    http_status = None
    response_size = 0
    html_text = ""

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            resp = await client.get(target_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
            })
            http_status = resp.status_code
            response_size = len(resp.content)
            html_text = resp.text
            print(f"2. HTTP Status: {http_status}")
            print(f"3. Response Size: {response_size} bytes ({response_size / 1024:.2f} KB)")
        except Exception as e:
            print(f"2. HTTP Status: ERROR ({e})")
            print("3. Response Size: 0 bytes")

    scripts = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', html_text, re.DOTALL)
    print(f"   application/ld+json script tags found: {len(scripts)}")

    provider = RainbowProvider()
    normalizer = RainbowNormalizer()

    raw_offers = await provider.fetch_offers()
    print(f"4. Parsed Raw Offers Count: {len(raw_offers)}")

    normalized_offers = []
    for raw in raw_offers:
        norm = normalizer.normalize(raw)
        if norm:
            normalized_offers.append(norm)

    print(f"5. Normalized Offers Count: {len(normalized_offers)}")
    flight_offers = [o for o in normalized_offers if o.transport_type == TransportType.FLIGHT]
    print(f"6. Saved Offers Count (DB simulation): {len(flight_offers)}")

    reason = None
    if http_status != 200:
        reason = f"Provider API returned HTTP status {http_status}"
    elif len(scripts) == 0:
        reason = "Parser failed: No `<script type=\"application/ld+json\">` tags found in returned HTML"
    elif len(raw_offers) == 0:
        reason = "Parser failed: No `@type: ItemList` or `@type: Product` objects found in ld+json scripts"
    elif len(normalized_offers) == 0:
        reason = "Normalization failed: All raw offer objects failed schema validation"

    print(f"7. Pipeline Stop Reason: {reason or 'Pipeline completed successfully'}")


async def diagnose_wakacje_pl():
    print("\n" + "=" * 80)
    print("DIAGNOSING WAKACJE.PL PROVIDER PIPELINE")
    print("=" * 80)

    target_url = "https://www.wakacje.pl/wczasy/hiszpania/"
    print(f"1. Outgoing Request URL / Params: {target_url}")

    http_status = None
    response_size = 0
    html_text = ""

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        try:
            resp = await client.get(target_url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
            })
            http_status = resp.status_code
            response_size = len(resp.content)
            html_text = resp.text
            print(f"2. HTTP Status: {http_status}")
            print(f"3. Response Size: {response_size} bytes ({response_size / 1024:.2f} KB)")
        except Exception as e:
            print(f"2. HTTP Status: ERROR ({e})")
            print("3. Response Size: 0 bytes")

    provider = WakacjePlProvider()
    normalizer = WakacjePlNormalizer()

    raw_offers = await provider.fetch_offers()
    print(f"4. Parsed Raw Offers Count: {len(raw_offers)}")

    normalized_offers = []
    for raw in raw_offers:
        norm = normalizer.normalize(raw)
        if norm:
            normalized_offers.append(norm)

    print(f"5. Normalized Offers Count: {len(normalized_offers)}")
    flight_offers = [o for o in normalized_offers if o.transport_type == TransportType.FLIGHT]
    print(f"6. Saved Offers Count (DB simulation): {len(flight_offers)}")

    reason = None
    if http_status != 200:
        reason = f"Provider API returned HTTP status {http_status}"
    elif len(raw_offers) == 0:
        reason = "Parser failed: No offer card links matching `/oferty/` found in HTML"

    print(f"7. Pipeline Stop Reason: {reason or 'Pipeline completed successfully'}")


async def main():
    await diagnose_itaka()
    await diagnose_tui()
    await diagnose_rainbow()
    await diagnose_wakacje_pl()


if __name__ == "__main__":
    asyncio.run(main())
