import asyncio
import json
import logging
import sys

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(level=logging.INFO)

from app.providers.tui.provider import TuiProvider
from app.providers.tui.normalizer import TuiNormalizer

from app.providers.itaka.provider import ItakaProvider
from app.providers.itaka.normalizer import ItakaNormalizer

from app.providers.rainbow.provider import RainbowProvider
from app.providers.rainbow.normalizer import RainbowNormalizer

from app.providers.wakacje_pl.provider import WakacjePlProvider
from app.providers.wakacje_pl.normalizer import WakacjePlNormalizer

from playwright.async_api import async_playwright

async def verify_operator(name, provider_cls, normalizer_cls, search_url):
    print(f"\n================================================================================")
    print(f"VERIFYING OPERATOR: {name.upper()}")
    print(f"================================================================================")
    
    # 1. Fragment pobranego HTML ze strony wyszukiwania
    print(f"1. FRAGMENT POBRANEGO HTML ({name}):")
    html_snippet = ""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        try:
            resp = await page.goto(search_url, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(3000)
            html = await page.content()
            html_snippet = html[:800]
            print(f"  [HTTP Status: {resp.status}] HTML Snippet ({len(html)} bytes):")
            print(f"  {html_snippet[:400]}...")
        except Exception as e:
            print(f"  Error fetching HTML snippet: {e}")
        await browser.close()

    # 2. Fetch raw offers using Importer Provider & show Fragment wyciągniętego JSON/DOM
    provider = provider_cls()
    normalizer = normalizer_cls()
    
    raw_offers = await provider.fetch_offers()
    print(f"\n-> Total Raw Offers Extracted: {len(raw_offers)}")
    if not raw_offers:
        print(f"❌ ERROR: 0 offers extracted for {name}!")
        return

    sample_raw = raw_offers[0]
    raw_json_str = json.dumps(sample_raw, indent=2, ensure_ascii=False)
    print(f"\n2. FRAGMENT WYCIĄGNIĘTEGO JSON/DOM ({name}):")
    print(raw_json_str[:1200] + ("..." if len(raw_json_str) > 1200 else ""))

    # 3. Wynik normalizacji
    normalized = normalizer.normalize(sample_raw)
    print(f"\n3. WYNIK NORMALIZACJI ({name}):")
    if normalized:
        print(normalized.model_dump_json(indent=2))
        offer_url = normalized.offer_url
    else:
        print(f"❌ Normalization failed for sample offer!")
        offer_url = None

    # 4. offer_url
    print(f"\n4. OFFER_URL ({name}):")
    print(offer_url)

    # 5. Otwarcie tego URL w przeglądarce
    if offer_url:
        print(f"\n5. OTWARCIE URL W PRZEGLĄDARCE ({name}):")
        print(f"  Navigating to direct offer URL: {offer_url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            try:
                resp = await page.goto(offer_url, wait_until="domcontentloaded", timeout=25000)
                await page.wait_for_timeout(3000)
                status = resp.status if resp else "None"
                title = await page.title()
                print(f"  Status odpowiedzi: {status}")
                print(f"  Tytuł załadowanej strony oferty: {title}")
                if status in [200, 301, 302]:
                    print(f"  ✅ SUCCESS: Strona oferty otworzyła się poprawnie (HTTP {status})!")
                else:
                    print(f"  ⚠️ Warning: HTTP Status {status}")
            except Exception as e:
                print(f"  ❌ Error opening URL in browser: {e}")
            await browser.close()

async def main():
    print("================================================================================")
    print("STARTING COMPLETE LIVE VERIFICATION FOR ALL 4 OPERATORS")
    print("================================================================================")
    
    await verify_operator("TUI", TuiProvider, TuiNormalizer, "https://www.tui.pl/wypoczynek/wyniki-wyszukiwania-samolot")
    await verify_operator("ITAKA", ItakaProvider, ItakaNormalizer, "https://www.itaka.pl/wyniki-wyszukiwania/wakacje/")
    await verify_operator("RAINBOW", RainbowProvider, RainbowNormalizer, "https://r.pl/szukaj")
    await verify_operator("WAKACJE.PL", WakacjePlProvider, WakacjePlNormalizer, "https://www.wakacje.pl/wczasy/")

if __name__ == "__main__":
    asyncio.run(main())
