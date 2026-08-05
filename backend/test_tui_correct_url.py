import asyncio
import json
import os
from playwright.async_api import async_playwright

OUT_DIR = os.path.join(os.path.dirname(__file__), "analysis_results", "tui_correct")

async def test_tui():
    os.makedirs(OUT_DIR, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()
        
        captured = []
        async def handle_response(response):
            url = response.url
            if "tui-search" in url or "offers" in url or "api" in url:
                try:
                    body = await response.text()
                    captured.append({
                        "url": url,
                        "status": response.status,
                        "headers": dict(response.headers),
                        "body_snippet": body[:50000],
                        "body_len": len(body)
                    })
                except Exception:
                    pass

        page.on("response", handle_response)
        
        url = "https://www.tui.pl/wypoczynek/wyniki-wyszukiwania-samolot"
        print(f"Navigating to TUI correct URL: {url}...")
        resp = await page.goto(url, wait_until="networkidle", timeout=30000)
        print(f"Response status: {resp.status if resp else 'None'}")
        
        await page.wait_for_timeout(5000)
        
        html = await page.content()
        with open(os.path.join(OUT_DIR, "page.html"), "w", encoding="utf-8") as f:
            f.write(html)
            
        with open(os.path.join(OUT_DIR, "api_responses.json"), "w", encoding="utf-8") as f:
            json.dump(captured, f, indent=2, ensure_ascii=False)
            
        print(f"Captured {len(captured)} TUI API responses!")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_tui())
