import asyncio
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

async def test_wakacje_card_dom():
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
        await page.wait_for_timeout(5000)
        
        # Get offer cards
        cards = await page.query_selector_all("[data-aria-label*='oferta'], [class*='offer'], article")
        print(f"Total cards: {len(cards)}")
        
        for idx, card in enumerate(cards[:5]):
            text = await card.inner_text()
            links = await card.query_selector_all("a[href]")
            hrefs = []
            for l in links:
                h = await l.get_attribute("href")
                if h:
                    hrefs.append(h)
            
            print(f"\n--- CARD #{idx} ---")
            print("  Text Snippet:", text.replace("\n", " | ")[:150])
            print("  Hrefs:", hrefs)
            
            # Check dataset / attributes of card
            attrs = await card.evaluate("""el => {
                let res = {};
                for (let attr of el.attributes) {
                    res[attr.name] = attr.value;
                }
                return res;
            }""")
            print("  Card Attributes:", attrs)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_wakacje_card_dom())
