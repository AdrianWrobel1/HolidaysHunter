import json
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

DIR = os.path.join(os.path.dirname(__file__), "analysis_results", "wakacje_search")
html_path = os.path.join(DIR, "page.html")

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

print(f"HTML len: {len(html)}")

# Search for any script containing offer data (e.g. hotel name, price, offer id, url)
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print(f"Total script tags: {len(scripts)}")

for idx, s in enumerate(scripts):
    s_clean = s.strip()
    if not s_clean:
        continue
    if any(kw in s_clean.lower() for kw in ["hotel", "price", "cena", "wczasy", "offer"]):
        if len(s_clean) > 500:
            print(f"\n[Script #{idx}] Len {len(s_clean)} B | Snippet: {s_clean[:300]}...")

# Search for DOM offer links in HTML
links = re.findall(r'href="(/oferty/[^"]+|/wczasy/[^"]+)"', html)
print(f"\nTotal offer-like hrefs in HTML: {len(links)}")
for l in set(links[:20]):
    print(" ", l)
