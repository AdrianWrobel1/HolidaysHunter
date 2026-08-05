import asyncio
import json
import re
from playwright.async_api import async_playwright

async def debug_tui_and_itaka():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        
        # 1. TUI
        page = await context.new_page()
        print("Fetching TUI via Playwright...")
        await page.goto("https://www.tui.pl/wypoczynek/wyniki-wyszukiwania-samolot", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        tui_html = await page.content()
        match_tui = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', tui_html)
        if match_tui:
            tui_data = json.loads(match_tui.group(1))
            offers_data = tui_data.get("props", {}).get("pageProps", {}).get("initialOffersData")
            offers_cnt = len(offers_data) if isinstance(offers_data, list) else len(offers_data.get("offers", [])) if isinstance(offers_data, dict) else 0
            print(f"TUI Playwright extracted {offers_cnt} offers from __NEXT_DATA__!")
        await page.close()

        # 2. ITAKA
        page = await context.new_page()
        print("Fetching ITAKA via Playwright...")
        await page.goto("https://www.itaka.pl/wyniki-wyszukiwania/wakacje/", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)
        itaka_html = await page.content()
        match_itaka = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', itaka_html)
        if match_itaka:
            itaka_data = json.loads(match_itaka.group(1))
            initial_qs = itaka_data.get("props", {}).get("pageProps", {}).get("initialQueryState", {})
            queries = initial_qs.get("queries", [])
            for q in queries:
                state_data = q.get("state", {}).get("data")
                if isinstance(state_data, dict):
                    main = state_data.get("main", {})
                    if isinstance(main, dict):
                        rates = main.get("rates", {})
                        if isinstance(rates, dict):
                            lst = rates.get("list", [])
                            if lst:
                                print(f"ITAKA Playwright extracted {len(lst)} offers from __NEXT_DATA__!")
                                break
        await page.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_tui_and_itaka())
