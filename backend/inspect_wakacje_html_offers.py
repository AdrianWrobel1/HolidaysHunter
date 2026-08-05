import json
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

DIR = os.path.join(os.path.dirname(__file__), "analysis_results", "wakacje_deep")
html_path = os.path.join(DIR, "..", "wakacje.pl", "page.html")

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

print(f"Wakacje.pl HTML size: {len(html)} bytes")

# Check if offer links exist in HTML
offer_hrefs = re.findall(r'href="(/oferty/[^"]+|/wczasy/[^"]+)"', html)
print(f"Offer hrefs found in HTML: {len(offer_hrefs)}")
for h in set(offer_hrefs[:20]):
    print(" ", h)

# Search HTML for offer data JSON structures or window state
scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
print(f"\nSearching {len(scripts)} scripts in HTML...")
for idx, s in enumerate(scripts):
    if "hotel" in s.lower() and ("cena" in s.lower() or "price" in s.lower() or "oferta" in s.lower()):
        print(f"  Script #{idx} (len {len(s)} B) snippet: {s[:250]}...")
