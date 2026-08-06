"""Deep inspection script to prove exact JSON paths and keys for ITAKA, TUI, and Rainbow."""

import asyncio
import json
import logging
import re
import sys

import httpx

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO)


async def inspect_itaka():
    print("\n" + "=" * 80)
    print("INSPECTING ITAKA __NEXT_DATA__ JSON PATHS")
    print("=" * 80)

    url = "https://www.itaka.pl/wyniki-wyszukiwania/wakacje/hiszpania/?order=popularity"
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', resp.text)
        if match:
            data = json.loads(match.group(1))
            page_props = data.get("props", {}).get("pageProps", {})
            print("ITAKA pageProps keys:", list(page_props.keys()))

            # Print sub-keys of pageProps
            for k, v in page_props.items():
                if isinstance(v, dict):
                    print(f"  pageProps.{k} keys:", list(v.keys())[:10])
                elif isinstance(v, list):
                    print(f"  pageProps.{k} list len:", len(v))


async def inspect_tui():
    print("\n" + "=" * 80)
    print("INSPECTING TUI __NEXT_DATA__ JSON PATHS")
    print("=" * 80)

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
        print("TUI pageProps keys:", list(page_props.keys()))
        for k, v in page_props.items():
            if isinstance(v, dict):
                print(f"  pageProps.{k} keys:", list(v.keys())[:10])
            elif isinstance(v, list):
                print(f"  pageProps.{k} list len:", len(v))


async def inspect_rainbow():
    print("\n" + "=" * 80)
    print("INSPECTING RAINBOW LD+JSON PRODUCT OBJECT KEYS")
    print("=" * 80)

    url = "https://r.pl/hiszpania"
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        })
        scripts = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', resp.text, re.DOTALL)
        for s in scripts:
            try:
                data = json.loads(s.strip())
                if isinstance(data, dict) and data.get("@type") == "ItemList":
                    items = data.get("itemListElement", [])
                    print(f"Rainbow ItemList len: {len(items)}")
                    if items:
                        sample_item = items[0].get("item", {})
                        print("Rainbow Sample Item Keys:", list(sample_item.keys()))
                        print("Rainbow Sample Item Payload:")
                        print(json.dumps(sample_item, indent=2, ensure_ascii=False))
            except Exception as e:
                print("Error parsing script:", e)


async def main():
    await inspect_itaka()
    await inspect_tui()
    await inspect_rainbow()


if __name__ == "__main__":
    asyncio.run(main())
