import os
import re

search_dir = os.path.dirname(__file__)

keywords = [
    "generate_fallback_offers",
    "mock_data",
    "TUI-LIVE",
    "ITAKA-LIVE",
    "RAINBOW-LIVE",
    "WAKACJE_PL-LIVE",
    "LIVE-",
    "fallback",
    "registry"
]

print("=== DEEP CODEBASE SEARCH FOR FALLBACK CALLS & STARTUP PROVIDERS ===")

for root, dirs, files in os.walk(search_dir):
    if ".venv" in root or ".pytest_cache" in root or "__pycache__" in root or "analysis_results" in root:
        continue
    for file in files:
        if file.endswith(".py") or file.endswith(".sql") or file.endswith(".json") or file.endswith(".md"):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                    for idx, line in enumerate(lines, 1):
                        for kw in keywords:
                            if kw.lower() in line.lower():
                                print(f"{filepath}:{idx} -> {line.strip()[:140]}")
            except Exception as e:
                pass
