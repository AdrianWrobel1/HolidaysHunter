import os
import sys

def search_text(root_dir, search_terms):
    print(f"Searching in {root_dir} for {search_terms}")
    for root, dirs, files in os.walk(root_dir):
        if any(ignore in root for ignore in ['node_modules', '.venv', '.git', '__pycache__', '.pytest_cache', 'egg-info']):
            continue
        for f in files:
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as file_content:
                    content = file_content.read()
                    for term in search_terms:
                        if term in content:
                            print(f"Match '{term}' in: {filepath}")
            except Exception as e:
                pass

if __name__ == "__main__":
    search_text("c:\\Users\\Adrian\\Desktop\\HolidaysHunter\\backend", ["google.com", "TUI-LIVE-004", "generate_fallback_offers"])
