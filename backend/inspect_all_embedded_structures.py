import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(__file__)
ANALYSIS_DIR = os.path.join(BASE_DIR, "analysis_results")

def examine_tui():
    print("\n========================================================")
    print("EXAMINING TUI DATA STRUCTURE")
    print("========================================================")
    html_path = os.path.join(ANALYSIS_DIR, "tui_correct", "page.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    import re
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if not match:
        print("TUI __NEXT_DATA__ not found!")
        return
        
    data = json.loads(match.group(1))
    page_props = data.get("props", {}).get("pageProps", {})
    offers_data = page_props.get("initialOffersData")
    if isinstance(offers_data, list):
        print(f"Total offers in TUI initialOffersData (list): {len(offers_data)}")
        if offers_data:
            print("\n--- SAMPLE TUI OFFER #0 ---")
            print(json.dumps(offers_data[0], indent=2, ensure_ascii=False)[:3000])
    elif isinstance(offers_data, dict):
        print(f"TUI initialOffersData keys: {list(offers_data.keys())}")
        offers = offers_data.get("offers", [])
        print(f"Total offers in TUI initialOffersData: {len(offers)}")
        if offers:
            print("\n--- SAMPLE TUI OFFER #0 ---")
            print(json.dumps(offers[0], indent=2, ensure_ascii=False)[:3000])

def examine_itaka():
    print("\n========================================================")
    print("EXAMINING ITAKA DATA STRUCTURE")
    print("========================================================")
    emb_path = os.path.join(ANALYSIS_DIR, "itaka", "embedded_data.json")
    with open(emb_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    next_d = data.get("__NEXT_DATA__", {})
    initial_qs = next_d.get("props", {}).get("pageProps", {}).get("initialQueryState", {})
    queries = initial_qs.get("queries", [])
    for q in queries:
        state_data = q.get("state", {}).get("data")
        if isinstance(state_data, dict):
            main = state_data.get("main", {})
            if isinstance(main, dict):
                rates = main.get("rates", {})
                if isinstance(rates, dict):
                    offer_list = rates.get("list", [])
                    print(f"Total offers in ITAKA React Query state: {len(offer_list)}")
                    if offer_list:
                        print("\n--- SAMPLE ITAKA OFFER #0 ---")
                        print(json.dumps(offer_list[0], indent=2, ensure_ascii=False)[:3000])

def examine_rainbow():
    print("\n========================================================")
    print("EXAMINING RAINBOW DATA STRUCTURE")
    print("========================================================")
    emb_path = os.path.join(ANALYSIS_DIR, "rainbow", "embedded_data.json")
    with open(emb_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    json_scripts = data.get("json_scripts", [])
    for s in json_scripts:
        content = s.get("content")
        if isinstance(content, dict) and content.get("@type") == "ItemList":
            items = content.get("itemListElement", [])
            print(f"Rainbow Schema.org ItemList length: {len(items)}")
            if items:
                print("\n--- SAMPLE RAINBOW SCHEMA.ORG ITEM #0 ---")
                print(json.dumps(items[0], indent=2, ensure_ascii=False))

def examine_wakacje():
    print("\n========================================================")
    print("EXAMINING WAKACJE.PL DATA STRUCTURE")
    print("========================================================")
    html_path = os.path.join(ANALYSIS_DIR, "wakacje.pl", "page.html")
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
        
    import re
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html)
    if match:
        data = json.loads(match.group(1))
        page_props = data.get("props", {}).get("pageProps", {})
        print(f"Wakacje.pl __NEXT_DATA__ pageProps keys: {list(page_props.keys())}")
        
    # Check if there are other json script tags or window state in Wakacje.pl HTML
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    for idx, s in enumerate(scripts):
        if "offers" in s or "wczasy" in s or "search" in s or "apollo" in s.lower() or "state" in s.lower():
            if len(s) > 500 and ("hotel" in s.lower() or "cena" in s.lower() or "price" in s.lower()):
                print(f"  Wakacje.pl Script #{idx} (len {len(s)} B) snippet: {s[:300]}...")

if __name__ == "__main__":
    examine_tui()
    examine_itaka()
    examine_rainbow()
    examine_wakacje()
