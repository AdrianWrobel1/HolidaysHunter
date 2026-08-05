import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "analysis_results")

def find_keys(obj, target_key, depth=0, max_depth=10):
    if depth > max_depth:
        return
    if isinstance(obj, dict):
        for k, v in obj.items():
            if target_key.lower() in k.lower():
                print(f"{'  '*depth}Key match: {k} (type: {type(v).__name__})")
                if isinstance(v, list):
                    print(f"{'  '*depth}  List length: {len(v)}")
                    if len(v) > 0 and isinstance(v[0], dict):
                        print(f"{'  '*depth}  First item keys: {list(v[0].keys())}")
                elif isinstance(v, dict):
                    print(f"{'  '*depth}  Dict keys: {list(v.keys())[:10]}")
            find_keys(v, target_key, depth+1, max_depth)
    elif isinstance(obj, list):
        for i, item in enumerate(obj[:3]):
            find_keys(item, target_key, depth+1, max_depth)

print("\n--- ITAKA PAGE PROPS SEARCH ---")
itaka_dump = os.path.join(RESULTS_DIR, "itaka", "page_props_dump.json")
if os.path.exists(itaka_dump):
    with open(itaka_dump, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("Searching 'offers' / 'results' in Itaka pageProps:")
    find_keys(data, "offer")
    find_keys(data, "result")
    find_keys(data, "hotel")

print("\n--- WAKACJE.PL PAGE PROPS SEARCH ---")
wakacje_dump = os.path.join(RESULTS_DIR, "wakacje.pl", "page_props_dump.json")
if os.path.exists(wakacje_dump):
    with open(wakacje_dump, "r", encoding="utf-8") as f:
        data = json.load(f)
    print("Searching 'offers' / 'results' / 'data' in Wakacje.pl pageProps:")
    find_keys(data, "offer")
    find_keys(data, "result")
    find_keys(data, "data")
