import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "analysis_results")

def analyze_html_and_embedded(op):
    print(f"\n=========================================")
    print(f"ANALYZING HTML & EMBEDDED FOR: {op.upper()}")
    print(f"=========================================")
    op_dir = os.path.join(RESULTS_DIR, op)
    
    # 1. Inspect embedded_data.json
    emb_path = os.path.join(op_dir, "embedded_data.json")
    if os.path.exists(emb_path):
        with open(emb_path, "r", encoding="utf-8") as f:
            emb = json.load(f)
            
        next_d = emb.get("__NEXT_DATA__")
        if next_d and isinstance(next_d, dict):
            # Dump JSON structure summary
            page = next_d.get("page")
            props = next_d.get("props", {}).get("pageProps", {})
            print(f"  __NEXT_DATA__ page: {page}")
            
            # Write pageProps keys and sample values to a file for examination
            with open(os.path.join(op_dir, "page_props_dump.json"), "w", encoding="utf-8") as out:
                json.dump(props, out, indent=2, ensure_ascii=False)
            print(f"  Dumped pageProps to {op_dir}/page_props_dump.json")

    # 2. Check HTML content for inline window state or scripts
    html_path = os.path.join(op_dir, "page.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
            print(f"  HTML file size: {len(html)} bytes")
            if "__NEXT_DATA__" in html:
                print("  Contains __NEXT_DATA__ tag")
            if "__NUXT__" in html or "__NUXT_DATA__" in html:
                print("  Contains __NUXT__ tag")

if __name__ == "__main__":
    for op in ["itaka", "wakacje.pl", "rainbow", "tui"]:
        analyze_html_and_embedded(op)
