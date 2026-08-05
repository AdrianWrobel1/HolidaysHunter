import os

search_dir = os.path.dirname(__file__)

print("=== PIPELINE TRACE SEARCH ===")

files_to_check = [
    "reimport_all.py",
    "verify_pipeline.py",
    "test_import.py",
    "app/services/import_service.py",
    "app/services/offer_service.py",
    "app/api/v1/offers.py",
    "app/api/endpoints/offers.py",
    "app/database/seed.py",
    "app/main.py"
]

for rel_path in files_to_check:
    full_path = os.path.join(search_dir, rel_path)
    if os.path.exists(full_path):
        print(f"\n--- {rel_path} ---")
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            for idx, line in enumerate(lines, 1):
                if any(w in line.lower() for w in ["fetch_offers", "fallback", "generate_fallback", "importer", "seed", "reimport", "mock"]):
                    print(f"  Line {idx}: {line.strip()[:140]}")
