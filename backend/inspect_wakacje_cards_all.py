import asyncio
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def find_wakacje_cards():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        url = "https://www.wakacje.pl/wczasy/"
        print(f"Navigating to Wakacje.pl: {url}...")
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(6000)
        
        # Search for elements containing "zł" or "opinii"
        els = await page.query_selector_all("a")
        print(f"Total <a> tags on page: {len(els)}")
        offer_links = []
        for a in els:
            href = await a.get_attribute("href")
            text = await a.inner_text()
            if href and any(k in href for k in ["oferta", "wczasy", "hotel", "p/"]):
                if len(text.strip()) > 0:
                    offer_links.append({"href": href, "text": text.strip()[:100]})
                    
        print(f"Offer links with text: {len(offer_links)}")
        for ol in offer_links[:15]:
            print(f"  Href: {ol['href']} | Text: {ol['text']}")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_wakacje_cards())
