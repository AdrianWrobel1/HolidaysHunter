import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "analysis_results", "tui_correct")

with open(os.path.join(RESULTS_DIR, "api_responses.json"), "r", encoding="utf-8") as f:
    resps = json.load(f)

print(f"Total TUI API responses captured: {len(resps)}")

for idx, r in enumerate(resps):
    url = r["url"]
    status = r["status"]
    snip = r["body_snippet"]
    print(f"\n[Response #{idx}] Status {status} | URL: {url}")
    print(f"  Snippet ({r['body_len']} B): {snip[:500]}...")

# Check page HTML for embedded data
with open(os.path.join(RESULTS_DIR, "page.html"), "r", encoding="utf-8") as f:
    html = f.read()

print(f"\nTUI HTML size: {len(html)} B")
if "__NEXT_DATA__" in html:
    print("HTML contains __NEXT_DATA__ tag")
    # Extract __NEXT_DATA__
    import re
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if match:
        data = json.loads(match.group(1))
        page = data.get("page")
        props = data.get("props", {}).get("pageProps", {})
        print(f"__NEXT_DATA__ page: {page}")
        print(f"__NEXT_DATA__ pageProps keys: {list(props.keys())}")
        if "initialSearchResult" in props or "offers" in str(props):
            print("Found offers in __NEXT_DATA__!")
