import asyncio
import json
import re
import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")


async def inspect_itaka_queries():
    url = "https://www.itaka.pl/wyniki-wyszukiwania/wakacje/hiszpania/?order=popularity"
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', resp.text)
        if match:
            data = json.loads(match.group(1))
            queries = data.get("props", {}).get("pageProps", {}).get("initialQueryState", {}).get("queries", [])
            print(f"ITAKA queries count: {len(queries)}")
            for idx, q in enumerate(queries):
                query_key = q.get("queryKey")
                state_data = q.get("state", {}).get("data")
                data_type = type(state_data).__name__
                keys = list(state_data.keys()) if isinstance(state_data, dict) else []
                print(f"  Query #{idx}: key={query_key[:3] if isinstance(query_key, list) else query_key} | data_type={data_type} | keys={keys[:5]}")
                if isinstance(state_data, dict) and "rates" in state_data:
                    rates = state_data["rates"]
                    print("  Found 'rates' key! Type:", type(rates).__name__)
                    if isinstance(rates, dict):
                        print("  rates keys:", list(rates.keys()))
                elif isinstance(state_data, dict) and "results" in state_data:
                    print("  Found 'results' key! Type:", type(state_data["results"]).__name__)


async def inspect_tui_top_offers():
    from playwright.async_api import async_playwright
    url = "https://www.tui.pl/wypoczynek/hiszpania"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        page = await browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)
        html = await page.content()
        await browser.close()

    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if match:
        data = json.loads(match.group(1))
        page_props = data.get("props", {}).get("pageProps", {})
        top_offers = page_props.get("initialTopOffersData", [])
        print(f"TUI initialTopOffersData len: {len(top_offers)}")
        if top_offers:
            print("TUI Sample Top Offer Keys:", list(top_offers[0].keys()))


async def main():
    await inspect_itaka_queries()
    await inspect_tui_top_offers()


if __name__ == "__main__":
    asyncio.run(main())
