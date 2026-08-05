import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app

def trace_execution():
    print("--- TRACING /api/offers EXECUTION ---")
    client = TestClient(app)
    response = client.get("/api/offers?page_size=100")
    data = response.json()
    offers = data.get("offers", [])
    print(f"Returned offers count: {len(offers)}")
    if offers:
        print("Sample offer keys:", list(offers[0].keys()))
        print("Sample offer offer_url:", offers[0].get("offer_url"))
    
    tui_004 = next((o for o in offers if o.get("external_id") == "TUI-LIVE-004"), None)
    if tui_004:
        print(f"Found TUI-LIVE-004 in /api/offers response: {tui_004}")
    else:
        print("TUI-LIVE-004 not found in page 1 response, checking all pages...")
        total_pages = data.get("total_pages", 1)
        for page in range(2, total_pages + 1):
            res = client.get(f"/api/offers?page_size=100&page={page}")
            d = res.json()
            for o in d.get("offers", []):
                if o.get("external_id") == "TUI-LIVE-004":
                    print(f"Found TUI-LIVE-004 on page {page}: {o}")

if __name__ == "__main__":
    trace_execution()
