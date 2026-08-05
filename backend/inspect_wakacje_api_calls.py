import asyncio
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

OUT_DIR = os.path.join(os.path.dirname(__file__), "analysis_results", "wakacje_search_api")

async def test_wakacje_interactive():
    from playwright.async_api import async_playwright
    os.makedirs(OUT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        all_reqs = []
        async def handle_request(request):
            if request.resource_type in ["fetch", "xhr"]:
                all_reqs.append({
                    "url": request.url,
                    "method": request.method,
                    "post_data": request.post_data,
                    "headers": dict(request.headers)
                })

        page.on("request", handle_request)
        
        # Navigate to main search page
        url = "https://www.wakacje.pl/wczasy/"
        print(f"Navigating to Wakacje.pl: {url}...")
        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        
        # Wait for network activity or DOM elements
        cards = await page.query_selector_all("[data-aria-label*='oferta'], [class*='offer'], article, a[href*='oferty']")
        print(f"Wakacje.pl cards count: {len(cards)}")
        
        # Save captured requests
        with open(os.path.join(OUT_DIR, "all_fetch_xhr.json"), "w", encoding="utf-8") as f:
            json.dump(all_reqs, f, indent=2, ensure_ascii=False)

        print(f"Captured {len(all_reqs)} Fetch/XHR requests!")
        
        # Inspect cards HTML snippet
        if cards:
            c0_html = await cards[0].inner_html()
            c0_text = await cards[0].inner_text()
            print(f"Card #0 Text: {c0_text[:200]}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_wakacje_interactive())
