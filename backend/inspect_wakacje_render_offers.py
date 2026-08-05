import asyncio
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def test_wakacje_rendered_offers():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        url = "https://www.wakacje.pl/wczasy/turcja/?od-2026-09-01,7-dni"
        print(f"Navigating to Wakacje.pl search URL: {url}...")
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(8000)
        
        # Scroll to ensure all cards are loaded
        await page.evaluate("window.scrollBy(0, 1000)")
        await page.wait_for_timeout(2000)
        
        # Query offer elements
        # On Wakacje.pl, offer cards have [data-test-id='offer-listing-card'] or similar
        cards = await page.query_selector_all("a[href*='/oferty/']")
        print(f"Found {len(cards)} links with '/oferty/' in href!")
        
        offers = []
        for idx, c in enumerate(cards):
            href = await c.get_attribute("href")
            text = await c.inner_text()
            offers.append({"href": href, "text": text.replace("\n", " | ")})
            
        print("\n--- FIRST 5 WAKACJE.PL RENDERED OFFERS ---")
        for o in offers[:5]:
            print(f"  Link: {o['href']}")
            print(f"  Text: {o['text'][:200]}\n")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_wakacje_rendered_offers())
