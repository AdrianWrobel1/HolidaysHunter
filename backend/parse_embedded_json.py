import asyncio
import json
import re
import httpx

URLS = {
    "TUI": "https://www.tui.pl/wypoczynek",
    "Rainbow": "https://r.pl/szukaj",
    "Wakacje.pl": "https://www.wakacje.pl/wczasy/",
    "Itaka": "https://www.itaka.pl/wyniki-wyszukiwania/wakacje/",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

async def inspect_embedded():
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=HEADERS) as client:
        for name, url in URLS.items():
            print(f"\n================ Extracting Embedded Data for {name} ================")
            try:
                r = await client.get(url)
                body = r.text

                # Check __NEXT_DATA__
                next_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', body, re.DOTALL)
                if next_match:
                    data = json.loads(next_match.group(1))
                    page_props = data.get("props", {}).get("pageProps", {})
                    print(f"[{name}] __NEXT_DATA__ extracted successfully!")
                    print(f"Top-level keys in pageProps: {list(page_props.keys())}")
                    
                    # Print sample offer key paths if found
                    serialized = json.dumps(page_props, ensure_ascii=False)
                    urls = re.findall(r'"(?:offerUrl|OfertaUrl|url|detailUrl|urlName)":\s*"([^"]+)"', serialized)
                    print(f"Found sample URL fields in __NEXT_DATA__: {urls[:5]}")

                # Check __NUXT__
                nuxt_match = re.search(r'window\.__NUXT__\s*=\s*(.*?);</script>', body, re.DOTALL)
                if nuxt_match:
                    print(f"[{name}] __NUXT__ script tag extracted!")
                    serialized = nuxt_match.group(1)
                    urls = re.findall(r'OfertaUrl:"([^"]+)"', serialized) or re.findall(r'url:"([^"]+)"', serialized)
                    print(f"Found sample URL fields in __NUXT__: {urls[:5]}")

            except Exception as e:
                print(f"Failed to extract for {name}: {e}")

if __name__ == "__main__":
    asyncio.run(inspect_embedded())
