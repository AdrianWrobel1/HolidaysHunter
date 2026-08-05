import sys, os
sys.path.insert(0, os.getcwd())
import httpx, json, re
from app.providers.itaka.provider import ItakaProvider

p_inst = ItakaProvider()

def fetch_country(slug):
    urls = [
        f"https://www.itaka.pl/wyniki-wyszukiwania/wakacje/{slug}/?order=popularity",
        f"https://www.itaka.pl/wyniki-wyszukiwania/wczasy/{slug}/?order=popularity",
        f"https://www.itaka.pl/wyniki-wyszukiwania/wakacje/{slug}/",
    ]
    for u in urls:
        try:
            r = httpx.get(u, headers={"User-Agent": "Mozilla/5.0"}, follow_redirects=True, timeout=10.0)
            offers = p_inst._extract_offers_from_html(r.text)
            if offers:
                return (u, len(offers))
        except Exception:
            pass
    return (urls[0], 0)

print("Dominikana (republika-dominikanska):", fetch_country("republika-dominikanska"))
print("Meksyk (meksyk):", fetch_country("meksyk"))
