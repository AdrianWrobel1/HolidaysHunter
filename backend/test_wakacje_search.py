import asyncio
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

OUT_DIR = os.path.join(os.path.dirname(__file__), "analysis_results", "wakacje_search")

async def test_wakacje_search():
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
                            "headers": dict(response.headers),
                            "body_snippet": body[:50000],
                            "body_len": len(body)
                        })
                    except Exception:
                        pass

        page.on("response", handle_response)
        
        url = "https://www.wakacje.pl/wczasy/turcja/?od-2026-09-01,7-dni"
        print(f"Navigating to Wakacje.pl search URL: {url}...")
        resp = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        print(f"Status: {resp.status if resp else 'None'}")
        
        await page.wait_for_timeout(7000)
        
        html = await page.content()
        with open(os.path.join(OUT_DIR, "page.html"), "w", encoding="utf-8") as f:
            f.write(html)
            
        with open(os.path.join(OUT_DIR, "xhr.json"), "w", encoding="utf-8") as f:
            json.dump(captured_xhr, f, indent=2, ensure_ascii=False)
            
        print(f"Captured {len(captured_xhr)} Wakacje.pl XHR responses!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_wakacje_search())
