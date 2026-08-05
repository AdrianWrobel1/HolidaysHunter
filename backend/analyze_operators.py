import asyncio
import json
import os
import re
from playwright.async_api import async_playwright

TARGETS = {
    "TUI": {
        "url": "https://www.tui.pl/wypoczynek/wyniki-wyszukiwania",
        "wait_selector": "article, .offer-tile, [data-testid='offer-card'], .offer-card",
    },
    "Rainbow": {
        "url": "https://r.pl/szukaj",
        "wait_selector": "[class*='offer'], [class*='karta'], article, a[href*='oferta']",
    },
    "Wakacje.pl": {
        "url": "https://www.wakacje.pl/wczasy/",
        "wait_selector": "[data-aria-label*='oferta'], [class*='offer-card'], article, a[href*='wczasy']",
    },
    "Itaka": {
        "url": "https://www.itaka.pl/wyniki-wyszukiwania/wakacje/",
        "wait_selector": "article, [class*='offer'], [data-testid*='offer']",
    }
}

OUT_DIR = os.path.join(os.path.dirname(__file__), "analysis_results")

async def analyze_operator(name, target, playwright):
    print(f"\n========================================================")
    print(f"STARTING ANALYSIS FOR: {name} -> {target['url']}")
    print(f"========================================================")

    operator_dir = os.path.join(OUT_DIR, name.lower())
    os.makedirs(operator_dir, exist_ok=True)

    browser = await playwright.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox"
        ]
    )

    context = await browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        viewport={"width": 1920, "height": 1080},
        locale="pl-PL",
        timezone_id="Europe/Warsaw"
    )

    page = await context.new_page()

    captured_requests = []

    async def handle_request(request):
        # We capture fetch, xhr, document, script, etc.
        req_data = {
            "url": request.url,
            "method": request.method,
            "resource_type": request.resource_type,
            "headers": dict(request.headers),
            "post_data": request.post_data,
        }
        # We will populate response later on response event
        captured_requests.append({
            "request": req_data,
            "response": None
        })

    async def handle_response(response):
        url = response.url
        # Find matching req
        for item in reversed(captured_requests):
            if item["request"]["url"] == url and item["response"] is None:
                body_str = ""
                try:
                    # Only try reading body for json, text, html or fetch/xhr
                    ct = response.headers.get("content-type", "").lower()
                    if any(t in ct for t in ["json", "text", "html", "javascript", "xml"]) or item["request"]["resource_type"] in ["fetch", "xhr", "document"]:
                        body_bytes = await response.body()
                        body_str = body_bytes.decode("utf-8", errors="ignore")
                except Exception as e:
                    body_str = f"<Could not read body: {e}>"

                item["response"] = {
                    "status": response.status,
                    "status_text": response.status_text,
                    "headers": dict(response.headers),
                    "body_snippet": body_str[:50000], # max 50KB snippet
                    "body_length": len(body_str)
                }
                break

    page.on("request", handle_request)
    page.on("response", handle_response)

    print(f"Navigating to {target['url']}...")
    try:
        response = await page.goto(target['url'], wait_until="networkidle", timeout=30000)
        print(f"Page initial response status: {response.status if response else 'None'}")
    except Exception as e:
        print(f"Page goto timeout/error: {e}")

    # Wait extra time for JS execution / lazy requests
    await page.wait_for_timeout(5000)

    # Scroll down to trigger lazy loading if needed
    try:
        await page.evaluate("window.scrollBy(0, 1000)")
        await page.wait_for_timeout(2000)
    except Exception:
        pass

    # Save HTML content
    html_content = await page.content()
    with open(os.path.join(operator_dir, "page.html"), "w", encoding="utf-8") as f:
        f.write(html_content)

    # Extract cookies
    cookies = await context.cookies()
    with open(os.path.join(operator_dir, "cookies.json"), "w", encoding="utf-8") as f:
        json.dump(cookies, f, indent=2, ensure_ascii=False)

    # Check for __NEXT_DATA__, __NUXT__, __NUXT_DATA__ or json scripts
    embedded_data = {}
    
    # 1. __NEXT_DATA__
    next_data_el = await page.query_selector("script#__NEXT_DATA__")
    if next_data_el:
        txt = await next_data_el.inner_text()
        try:
            embedded_data["__NEXT_DATA__"] = json.loads(txt)
        except Exception as e:
            embedded_data["__NEXT_DATA__"] = f"Parse error: {e}"

    # 2. __NUXT__ / __NUXT_DATA__
    nuxt_data_el = await page.query_selector("script#__NUXT_DATA__")
    if nuxt_data_el:
        txt = await nuxt_data_el.inner_text()
        try:
            embedded_data["__NUXT_DATA__"] = json.loads(txt)
        except Exception:
            embedded_data["__NUXT_DATA__"] = txt[:5000]

    # Evaluate window.__NUXT__ if present
    try:
        window_nuxt = await page.evaluate("window.__NUXT__")
        if window_nuxt:
            embedded_data["window.__NUXT__"] = str(window_nuxt)[:5000]
    except Exception:
        pass

    # 3. Other application/json scripts
    json_scripts = await page.query_selector_all("script[type='application/json'], script[type='application/ld+json']")
    embedded_data["json_scripts"] = []
    for idx, script in enumerate(json_scripts):
        id_attr = await script.get_attribute("id") or f"script_{idx}"
        txt = await script.inner_text()
        try:
            embedded_data["json_scripts"].append({"id": id_attr, "content": json.loads(txt)})
        except Exception:
            embedded_data["json_scripts"].append({"id": id_attr, "content": txt[:1000]})

    with open(os.path.join(operator_dir, "embedded_data.json"), "w", encoding="utf-8") as f:
        json.dump(embedded_data, f, indent=2, ensure_ascii=False)

    # Extract DOM links to offer cards
    anchors = await page.query_selector_all("a[href]")
    links = []
    for a in anchors:
        href = await a.get_attribute("href")
        text = await a.inner_text()
        if href and len(href.strip()) > 0:
            links.append({"href": href, "text": text.strip()[:100]})

    with open(os.path.join(operator_dir, "dom_links.json"), "w", encoding="utf-8") as f:
        json.dump(links[:200], f, indent=2, ensure_ascii=False)

    # Save network requests
    with open(os.path.join(operator_dir, "network_requests.json"), "w", encoding="utf-8") as f:
        json.dump(captured_requests, f, indent=2, ensure_ascii=False)

    print(f"Analysis for {name} complete! Captured {len(captured_requests)} requests.")
    print(f"Embedded data keys: {list(embedded_data.keys())}")
    print(f"Saved artifacts to {operator_dir}")

    await browser.close()

async def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    async with async_playwright() as p:
        for name, target in TARGETS.items():
            await analyze_operator(name, target, p)

if __name__ == "__main__":
    asyncio.run(main())
