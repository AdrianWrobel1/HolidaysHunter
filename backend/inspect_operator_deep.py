import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "analysis_results")

def inspect_itaka():
    print("\n========================================================")
    print("INSPECTING ITAKA")
    print("========================================================")
    path = os.path.join(RESULTS_DIR, "itaka", "embedded_data.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    next_data = data.get("__NEXT_DATA__", {})
    page_props = next_data.get("props", {}).get("pageProps", {})
    print("ITAKA pageProps keys:", list(page_props.keys()))
    
    # Check if offers exist in pageProps
    def find_offers_in_dict(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                if "offer" in k.lower() or "hotel" in k.lower() or "results" in k.lower() or "items" in k.lower():
                    if isinstance(v, list) and len(v) > 0:
                        print(f"Found list at {new_path}: length {len(v)}, sample item keys: {list(v[0].keys()) if isinstance(v[0], dict) else type(v[0])}")
                find_offers_in_dict(v, new_path)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj[:3]):
                find_offers_in_dict(item, f"{path}[{idx}]")

    find_offers_in_dict(page_props)

def inspect_wakacje():
    print("\n========================================================")
    print("INSPECTING WAKACJE.PL")
    print("========================================================")
    path = os.path.join(RESULTS_DIR, "wakacje.pl", "embedded_data.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    next_data = data.get("__NEXT_DATA__", {})
    page_props = next_data.get("props", {}).get("pageProps", {})
    print("Wakacje.pl pageProps keys:", list(page_props.keys()))
    
    def find_offers_in_dict(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                if "offer" in k.lower() or "hotel" in k.lower() or "results" in k.lower() or "items" in k.lower() or "data" in k.lower():
                    if isinstance(v, list) and len(v) > 0:
                        print(f"Found list at {new_path}: length {len(v)}, sample item: {list(v[0].keys()) if isinstance(v[0], dict) else type(v[0])}")
                find_offers_in_dict(v, new_path)
        elif isinstance(obj, list):
            for idx, item in enumerate(obj[:2]):
                find_offers_in_dict(item, f"{path}[{idx}]")

    find_offers_in_dict(page_props)

def inspect_rainbow():
    print("\n========================================================")
    print("INSPECTING RAINBOW")
    print("========================================================")
    path = os.path.join(RESULTS_DIR, "rainbow", "embedded_data.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    nuxt_data = data.get("__NUXT_DATA__", [])
    print(f"Rainbow __NUXT_DATA__ elements count: {len(nuxt_data)}")
    
    # Search for network requests that fetch offers
    net_path = os.path.join(RESULTS_DIR, "rainbow", "network_requests.json")
    with open(net_path, "r", encoding="utf-8") as f:
        net = json.load(f)
    
    print("Rainbow API requests:")
    for item in net:
        url = item["request"]["url"]
        if "api" in url or "graphql" in url or "szukaj" in url or "blok" in url or "r.pl" in url:
            if not any(ig in url for ig in ["static", "font", "css", "js", "png", "jpg", "svg", "google", "metrics"]):
                print(f"  {item['request']['method']} {url}")

def inspect_tui():
    print("\n========================================================")
    print("INSPECTING TUI")
    print("========================================================")
    net_path = os.path.join(RESULTS_DIR, "tui", "network_requests.json")
    with open(net_path, "r", encoding="utf-8") as f:
        net = json.load(f)
    
    print("TUI API requests:")
    for item in net:
        url = item["request"]["url"]
        if "tui.pl/api" in url:
            resp = item.get("response") or {}
            print(f"  {item['request']['method']} {url} -> Status: {resp.get('status')}")
            if item["request"].get("post_data"):
                print(f"     Payload: {item['request']['post_data']}")

if __name__ == "__main__":
    inspect_itaka()
    inspect_wakacje()
    inspect_rainbow()
    inspect_tui()
