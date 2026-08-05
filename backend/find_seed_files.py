import os

search_dir = os.path.dirname(__file__)

print("=== SEARCHING FOR SEED / BOOTSTRAP / SCHEDULER / INITIAL DATA ===")
for root, dirs, files in os.walk(search_dir):
    if ".venv" in root or ".pytest_cache" in root or "__pycache__" in root:
        continue
    for file in files:
        if file.endswith(".py"):
            filepath = os.path.join(root, file)
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
                if any(k in content.lower() for k in ["seed", "mock_data", "generate_fallback_offers", "live-00", "royal bodrum"]):
                    print(f"Match in: {filepath}")
