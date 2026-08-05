import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DIR = os.path.join(os.path.dirname(__file__), "analysis_results", "wakacje_deep")

# 1. Inspect window state
with open(os.path.join(DIR, "window_state.json"), "r", encoding="utf-8") as f:
    ws = json.load(f)

print("Wakacje.pl Window State top keys:", list(ws.keys()))
page_props = ws.get("props", {}).get("pageProps", {})
print("Wakacje.pl pageProps keys:", list(page_props.keys()))

# Search window state for offers / hotels
def search_offers(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            np = f"{path}.{k}" if path else k
            if any(kw in k.lower() for kw in ["offer", "hotel", "result", "search"]):
                if isinstance(v, list) and len(v) > 0:
                    print(f"Found list at {np}: len {len(v)}, sample item keys: {list(v[0].keys()) if isinstance(v[0], dict) else type(v[0])}")
            search_offers(v, np)
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:2]):
            search_offers(item, f"{path}[{i}]")

search_offers(ws)

# 2. Inspect DOM links
with open(os.path.join(DIR, "dom_links.json"), "r", encoding="utf-8") as f:
    links = json.load(f)

print(f"\nTotal DOM links captured: {len(links)}")
for l in links[:10]:
    print(f"  Href: {l['href']} | Text: {l['text']}")

# 3. Inspect XHR responses
with open(os.path.join(DIR, "xhr_responses.json"), "r", encoding="utf-8") as f:
    xhrs = json.load(f)

print(f"\nTotal XHR responses captured: {len(xhrs)}")
for x in xhrs:
    url = x["url"]
    if "api" in url or "v2" in url or "graphql" in url or "wczasy" in url:
        print(f"  {x['method']} {url} -> Status {x['status']}")
        print(f"    Snippet: {x['body_snippet'][:300]}...")
