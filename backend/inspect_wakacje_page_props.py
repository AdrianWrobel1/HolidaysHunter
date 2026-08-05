import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

DIR = os.path.join(os.path.dirname(__file__), "analysis_results", "wakacje_search")

with open(os.path.join(DIR, "page_props.json"), "r", encoding="utf-8") as f:
    props = json.load(f)

print("Wakacje.pl Search pageProps top keys:", list(props.keys()))

def find_offers_in_props(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            np = f"{path}.{k}" if path else k
            if any(kw in k.lower() for kw in ["offer", "hotel", "result", "search", "data", "list", "items"]):
                if isinstance(v, list) and len(v) > 0:
                    print(f"Found list at {np}: len {len(v)}, sample item keys: {list(v[0].keys()) if isinstance(v[0], dict) else type(v[0])}")
            find_offers_in_props(v, np)
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:2]):
            find_offers_in_props(item, f"{path}[{i}]")

find_offers_in_props(props)
