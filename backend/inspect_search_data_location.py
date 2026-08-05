import json
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "analysis_results")

def find_in_html(op):
    print(f"\n========================================================")
    print(f"LOCATING DATA IN HTML FOR: {op.upper()}")
    print(f"========================================================")
    html_path = os.path.join(RESULTS_DIR, op, "page.html")
    if not os.path.exists(html_path):
        print("HTML file missing.")
        return

    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Search for scripts containing JSON data or window state variables
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    print(f"Total script tags found in HTML: {len(scripts)}")
    
    for idx, s in enumerate(scripts):
        s_clean = s.strip()
        if not s_clean:
            continue
        # Look for indicators of offer lists (hotel names, prices, offer ids, dates)
        if any(k in s_clean for k in ["Casa Mare", "Crystal Paraiso", "RMFTULR", "AYTCRYP", "items", "offers", "results", "__STATE__", "__INITIAL_STATE__", "__APOLLO_STATE__"]):
            print(f"  [Script #{idx}] Length {len(s_clean)} B | Snippet: {s_clean[:200]}...")
            if "__APOLLO_STATE__" in s_clean or "__STATE__" in s_clean or "window." in s_clean:
                print(f"    Possible state script found! Save to file...")
                with open(os.path.join(RESULTS_DIR, op, f"script_state_{idx}.txt"), "w", encoding="utf-8") as out:
                    out.write(s_clean[:100000])

if __name__ == "__main__":
    for op in ["itaka", "wakacje.pl", "rainbow", "tui"]:
        find_in_html(op)
