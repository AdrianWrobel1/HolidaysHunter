"""Standalone CLI runner for End-to-End Live Integration Test.

Executes real provider import pipeline, clears previous dataset, calculates expected offer count from freshly imported database data, and compares against /api/offers HTTP endpoint.
"""

import asyncio
import os
import sys

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

from tests.test_live_e2e_integration import test_live_e2e_import_and_offers_filtering

if __name__ == "__main__":
    print("================================================================================")
    print("RUNNING STANDALONE E2E LIVE INTEGRATION TEST RUNNER")
    print("================================================================================")
    try:
        asyncio.run(test_live_e2e_import_and_offers_filtering())
        print("\n✅ ALL E2E LIVE INTEGRATION TESTS PASSED SUCCESSFULLY!")
    except Exception as exc:
        print(f"\n❌ E2E INTEGRATION TEST ENCOUNTERED FAILURES / ERROR: {exc}")
        sys.exit(1)
