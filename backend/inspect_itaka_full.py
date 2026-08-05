import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "analysis_results", "itaka")

with open(os.path.join(RESULTS_DIR, "embedded_data.json"), "r", encoding="utf-8") as f:
    emb = json.load(f)

print("ITAKA Embedded Data keys:", list(emb.keys()))

def search_json(obj, target_str):
    matches = []
    def recurse(o, path=""):
        if isinstance(o, str):
            if target_str.lower() in o.lower():
                matches.append((path, o[:200]))
        elif isinstance(o, dict):
            for k, v in o.items():
                recurse(v, f"{path}.{k}" if path else k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                recurse(v, f"{path}[{i}]")
    recurse(obj)
    return matches

m = search_json(emb, "Casa Mare")
print(f"Matches for 'Casa Mare' in embedded_data: {len(m)}")
for p, snippet in m[:5]:
    print(f"  Path: {p} -> {snippet}")

with open(os.path.join(RESULTS_DIR, "network_requests.json"), "r", encoding="utf-8") as f:
    net = json.load(f)

print(f"\nSearching network requests ({len(net)} total)...")
for item in net:
    url = item["request"]["url"]
    resp = item.get("response") or {}
    snip = resp.get("body_snippet", "")
    if "RMFTULR" in snip or "Casa Mare" in snip or "graphql" in url or "search" in url or "api" in url:
        print(f"Found in network request: {item['request']['method']} {url}")
        print(f"  Status: {resp.get('status')}")
        print(f"  Body length: {resp.get('body_length')}")
        print(f"  Snippet: {snip[:400]}")
