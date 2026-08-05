import asyncio
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

OUT_DIR = os.path.join(os.path.dirname(__file__), "analysis_results", "wakacje_deep")

async def test_wakacje():
    from playwright.async_api import async_playwright
    os.makedirs(OUT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        captured_xhr = []
        async def handle_response(response):
            req = response.request
            if req.resource_type in ["fetch", "xhr"]:
                url = req.url
                if not any(ig in url for ig in ["google", "facebook", "sentry", "hotjar", "clarity", "telemetry"]):
                    try:
                        body = await response.text()
                        captured_xhr.append({
                            "url": url,
                            "method": req.method,
                            "status": response.status,
                            "body_snippet": body[:50000],
                            "body_len": len(body)
                        })
                    except Exception:
                        pass

        page.on("response", handle_response)
        
        url = "https://www.wakacje.pl/wczasy/"
        print(f"Navigating to Wakacje.pl: {url}...")
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print(f"Wakacje.pl status: {resp.status if resp else 'None'}")
        
        await page.wait_for_timeout(6000)
        
        # Scroll down
        await page.evaluate("window.scrollBy(0, 1000)")
        await page.wait_for_timeout(3000)
        
        # Extract offer card hrefs from DOM
        cards = await page.query_selector_all("a[href*='oferta'], a[href*='wczasy']")
        card_links = []
        for c in cards:
            href = await c.get_attribute("href")
            text = await c.inner_text()
            if href:
                card_links.append({"href": href, "text": text.strip()[:100]})
                
        print(f"Found {len(card_links)} offer links in Wakacje.pl DOM!")
        
        with open(os.path.join(OUT_DIR, "dom_links.json"), "w", encoding="utf-8") as f:
            json.dump(card_links, f, indent=2, ensure_ascii=False)
            
        with open(os.path.join(OUT_DIR, "xhr_responses.json"), "w", encoding="utf-8") as f:
            json.dump(captured_xhr, f, indent=2, ensure_ascii=False)
            
        # Check window state in browser page
        window_apollo = await page.evaluate("window.__APOLLO_STATE__ || window.__NEXT_DATA__ || window.__STATE__")
        if window_apollo:
            with open(os.path.join(OUT_DIR, "window_state.json"), "w", encoding="utf-8") as f:
                json.dump(window_apollo, f, indent=2, ensure_ascii=False)
            print("Successfully dumped window state for Wakacje.pl!")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_wakacje())
