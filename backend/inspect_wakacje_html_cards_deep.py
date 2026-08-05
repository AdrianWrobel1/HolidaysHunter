import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')

DIR = os.path.join(os.path.dirname(__file__), "analysis_results", "wakacje_search")
html_path = os.path.join(DIR, "page.html")

with open(html_path, "r", encoding="utf-8") as f:
    html = f.read()

print(f"HTML size: {len(html)} bytes")

# Find occurrences of "zł" or "od " or "All Inclusive"
matches = [m.start() for m in re.finditer(r'All Inclusive|Ultra All Inclusive|Coral Travel|zł', html)]
print(f"Total matches found in HTML: {len(matches)}")

for m in matches[:5]:
    snippet = html[max(0, m-200):min(len(html), m+300)]
    print(f"\n--- MATCH AT INDEX {m} ---")
    print(snippet)
