import json
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

DIR = os.path.join(os.path.dirname(__file__), "analysis_results", "wakacje_search")

# 1. Inspect HTML __NEXT_DATA__
with open(os.path.join(DIR, "page.html"), "r", encoding="utf-8") as f:
    html = f.read()

print(f"Wakacje.pl Search HTML size: {len(html)} bytes")

match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
if match:
    data = json.loads(match.group(1))
    page = data.get("page")
    props = data.get("props", {}).get("pageProps", {})
    print(f"__NEXT_DATA__ page: {page}")
    print(f"__NEXT_DATA__ pageProps top keys: {list(props.keys())}")
    
    # Save pageProps to json dump
    with open(os.path.join(DIR, "page_props.json"), "w", encoding="utf-8") as out:
        json.dump(props, out, indent=2, ensure_ascii=False)
    print("Dumped Wakacje.pl search pageProps to page_props.json")

# 2. Inspect XHR responses
with open(os.path.join(DIR, "xhr.json"), "r", encoding="utf-8") as f:
    xhr = json.load(f)

print(f"\nTotal Captured XHR responses: {len(xhr)}")
for x in xhr:
    url = x["url"]
    status = x["status"]
    snip = x["body_snippet"]
    print(f"\n  [XHR] {x['method']} {url} -> Status {status}")
    print(f"   Snippet ({x['body_len']} B): {snip[:300]}...")
