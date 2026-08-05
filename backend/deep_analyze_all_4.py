import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "analysis_results")

def analyze_itaka():
    print("========================================================")
    print("1. ITAKA DEEP ANALYSIS")
    print("========================================================")
    path = os.path.join(RESULTS_DIR, "itaka", "embedded_data.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    next_d = data.get("__NEXT_DATA__", {})
    initial_qs = next_d.get("props", {}).get("pageProps", {}).get("initialQueryState", {})
    queries = initial_qs.get("queries", [])
    print(f"Total React Query queries in __NEXT_DATA__: {len(queries)}")
    
    for idx, q in enumerate(queries):
        query_key = q.get("queryKey")
        state_data = q.get("state", {}).get("data")
        print(f"\n[Query #{idx}] Key: {query_key}")
        if isinstance(state_data, dict):
            print(f"  Data keys: {list(state_data.keys())}")
            main = state_data.get("main", {})
            if isinstance(main, dict):
                rates = main.get("rates", {})
                if isinstance(rates, dict):
                    offer_list = rates.get("list", [])
                    print(f"  SUCCESS! Found 'rates.list' with {len(offer_list)} offers!")
                    if len(offer_list) > 0:
                        first_offer = offer_list[0]
                        print("  Sample Offer Fields:")
                        print(json.dumps(first_offer, indent=2, ensure_ascii=False)[:2000])

def analyze_rainbow():
    print("\n========================================================")
    print("2. RAINBOW DEEP ANALYSIS")
    print("========================================================")
    path = os.path.join(RESULTS_DIR, "rainbow", "embedded_data.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    # Check ld+json scripts in embedded data
    json_scripts = data.get("json_scripts", [])
    print(f"Total JSON scripts in Rainbow: {len(json_scripts)}")
    for s in json_scripts:
        content = s.get("content")
        if isinstance(content, dict) and content.get("@type") == "ItemList":
            items = content.get("itemListElement", [])
            print(f"  SUCCESS! Found Schema.org ItemList with {len(items)} offers in HTML!")
            if len(items) > 0:
                print("  Sample Item:")
                print(json.dumps(items[0], indent=2, ensure_ascii=False))

    # Also check __NUXT_DATA__ or Rainbow API endpoints
    net_path = os.path.join(RESULTS_DIR, "rainbow", "network_requests.json")
    with open(net_path, "r", encoding="utf-8") as f:
        net = json.load(f)

    # Let's see if Rainbow loaded offers via XHR or __NUXT_DATA__
    nuxt_data = data.get("__NUXT_DATA__", [])
    print(f"  __NUXT_DATA__ length: {len(nuxt_data)}")

def analyze_wakacje():
    print("\n========================================================")
    print("3. WAKACJE.PL DEEP ANALYSIS")
    print("========================================================")
    # Wakacje.pl search API or GraphQL
    net_path = os.path.join(RESULTS_DIR, "wakacje.pl", "network_requests.json")
    with open(net_path, "r", encoding="utf-8") as f:
        net = json.load(f)

    print(f"Total network requests captured for Wakacje.pl: {len(net)}")
    graphql_reqs = [r for r in net if "graphql" in r["request"]["url"].lower() or "api" in r["request"]["url"].lower() or "v1" in r["request"]["url"].lower()]
    print(f"API/GraphQL requests for Wakacje.pl: {len(graphql_reqs)}")
    
    for r in graphql_reqs:
        req = r["request"]
        resp = r.get("response") or {}
        url = req["url"]
        if not any(ig in url for ig in ["google", "facebook", "sentry", "hotjar", "clarity"]):
            print(f"  {req['method']} {url} -> Status {resp.get('status')}")
            if req.get("post_data"):
                print(f"    Payload: {req['post_data'][:300]}")
            snip = resp.get("body_snippet", "")
            if len(snip) > 0:
                print(f"    Resp snippet ({resp.get('body_length')} B): {snip[:300]}...")

if __name__ == "__main__":
    analyze_itaka()
    analyze_rainbow()
    analyze_wakacje()
