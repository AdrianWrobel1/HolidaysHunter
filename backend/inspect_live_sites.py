import asyncio
import httpx

URLS = {
    "TUI": "https://www.tui.pl/wypoczynek/wyniki-wyszukiwania",
    "Rainbow": "https://r.pl/szukaj",
    "Wakacje.pl": "https://www.wakacje.pl/wczasy/",
    "Itaka": "https://www.itaka.pl/wyniki-wyszukiwania/wakacje/",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
}

async def inspect():
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, headers=HEADERS) as client:
        for name, url in URLS.items():
            print(f"\n================ Inspecting {name} ({url}) ================")
            try:
                r = await client.get(url)
                print(f"Status Code: {r.status_code}")
                print(f"Final URL: {r.url}")
                print(f"Content-Type: {r.headers.get('content-type', '')}")
                print(f"Server: {r.headers.get('server', '')}")
                
                body = r.text
                has_next = "__NEXT_DATA__" in body
                has_nuxt = "__NUXT__" in body or "__NUXT_DATA__" in body
                has_cloudflare = "just a moment" in body.lower() or "cf-ray" in r.headers
                has_graphql = "graphql" in body.lower()
                has_json_script = 'type="application/json"' in body or 'type="application/ld+json"' in body

                print(f"Contains __NEXT_DATA__: {has_next}")
                print(f"Contains __NUXT__: {has_nuxt}")
                print(f"Contains GraphQL references: {has_graphql}")
                print(f"Contains Embedded JSON scripts: {has_json_script}")
                print(f"Cloudflare challenged/detected: {has_cloudflare}")
                print(f"Response HTML size: {len(body)} bytes")
                
                if has_next:
                    print("Sample __NEXT_DATA__ snippet found!")
                if "cf-mitigated" in r.headers or "cf-ray" in r.headers:
                    print(f"CF-Ray Header: {r.headers.get('cf-ray')}")
            except Exception as e:
                print(f"Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(inspect())
