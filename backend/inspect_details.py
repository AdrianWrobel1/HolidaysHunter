import json
import os
import sys

# Ensure UTF-8 output encoding for print
sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "analysis_results")

def analyze_operator_data(op_name):
    op_dir = os.path.join(RESULTS_DIR, op_name)
    print(f"\n========================================================")
    print(f"DETAILED ANALYSIS FOR: {op_name.upper()}")
    print(f"========================================================")
    
    # 1. Embedded data analysis
    emb_path = os.path.join(op_dir, "embedded_data.json")
    if os.path.exists(emb_path):
        with open(emb_path, "r", encoding="utf-8") as f:
            emb = json.load(f)
            print(f"Embedded Data Keys: {list(emb.keys())}")
            
            # Check __NEXT_DATA__
            if "__NEXT_DATA__" in emb and isinstance(emb["__NEXT_DATA__"], dict):
                next_d = emb["__NEXT_DATA__"]
                print(f"__NEXT_DATA__ page: {next_d.get('page')}")
                print(f"__NEXT_DATA__ buildId: {next_d.get('buildId')}")
                props = next_d.get("props", {})
                print(f"__NEXT_DATA__ props top keys: {list(props.keys())}")
                page_props = props.get("pageProps", {})
                print(f"__NEXT_DATA__ pageProps top keys: {list(page_props.keys())}")
                
            # Check __NUXT_DATA__
            if "__NUXT_DATA__" in emb:
                nuxt_d = emb["__NUXT_DATA__"]
                print(f"__NUXT_DATA__ type: {type(nuxt_d)}")
                if isinstance(nuxt_d, list):
                    print(f"__NUXT_DATA__ array length: {len(nuxt_d)}")
                    # Sample some strings/dicts from nuxt data array
                    sample_str = [x for x in nuxt_d if isinstance(x, str) and ("hotel" in x.lower() or "cena" in x.lower() or "oferta" in x.lower() or "pln" in x.lower() or "r.pl" in x.lower() or "term" in x.lower())]
                    print(f"__NUXT_DATA__ matching key snippets count: {len(sample_str)}")
                    print(f"Sample snippets: {sample_str[:10]}")

    # 2. Network requests analysis
    net_path = os.path.join(op_dir, "network_requests.json")
    if os.path.exists(net_path):
        with open(net_path, "r", encoding="utf-8") as f:
            net = json.load(f)
            print(f"\nTotal Captured Requests: {len(net)}")
            
            fetch_xhr = [r for r in net if r["request"]["resource_type"] in ["fetch", "xhr"]]
            print(f"Fetch/XHR Requests Count: {len(fetch_xhr)}")
            
            for item in fetch_xhr:
                req = item["request"]
                resp = item.get("response") or {}
                url = req["url"]
                method = req["method"]
                status = resp.get("status")
                body_snip = resp.get("body_snippet", "")
                
                # Filter out obvious analytics / static assets
                if any(ignored in url for ignored in ["google", "facebook", "doubleclick", "analytics", "metrics", "hotjar", "clarity", "sentry", "criteo"]):
                    continue
                    
                print(f"\n  [XHR/FETCH] {method} {url} -> Status: {status}")
                print(f"   Req Headers: {req['headers']}")
                if req.get("post_data"):
                    print(f"   POST Payload: {req['post_data'][:500]}")
                print(f"   Resp Body Snippet ({resp.get('body_length', 0)} B): {body_snip[:500]}")

    # 3. DOM Links
    dom_path = os.path.join(op_dir, "dom_links.json")
    if os.path.exists(dom_path):
        with open(dom_path, "r", encoding="utf-8") as f:
            links = json.load(f)
            offer_links = [l for l in links if any(k in l['href'].lower() for k in ['oferta', 'wczasy', 'wycieczka', 'hotel', 'p/'])]
            print(f"\nTotal DOM Links: {len(links)}, Offer-like links: {len(offer_links)}")
            for ol in offer_links[:10]:
                print(f"   Link: {ol['href']} | Text: {ol['text'][:50]}")

if __name__ == "__main__":
    for op in ["tui", "rainbow", "wakacje.pl", "itaka"]:
        analyze_operator_data(op)
