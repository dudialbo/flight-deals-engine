"""
Local runner for the deal categories refresh job.
Writes output to output/deals/ as JSON files for inspection.

Usage:
    SEARCH_BACKEND_BASE_URL=https://... python scripts/run_local_hot_deals.py
"""
import json
import os
import sys

# Allow running from project root without installing the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from flight_deals_engine.config.settings import Settings
from flight_deals_engine.jobs.refresh_deal_categories import run
from flight_deals_engine.observability.logging import configure_logging


if __name__ == "__main__":
    configure_logging("INFO")

    settings = Settings()
    settings.STORAGE_ADAPTER = "json"

    print("Running Deal Categories Refresh locally...")
    print(f"Origin: {settings.DEFAULT_ORIGIN}")
    print(f"Hot-deals destinations: {settings.HOT_DEALS_DESTINATIONS}")
    print()

    result = run(settings)

    print("\n--- Job Result ---")
    print(json.dumps(result, indent=2, default=str))

    print("\n--- Written files ---")
    deals_dir = os.path.join("output", "deals")
    if os.path.isdir(deals_dir):
        for fname in sorted(os.listdir(deals_dir)):
            fpath = os.path.join(deals_dir, fname)
            with open(fpath, encoding="utf-8") as f:
                data = json.load(f)
            if fname == "manifest.json":
                cats = data.get("categories", [])
                print(f"  manifest.json — {len(cats)} categories: {[c['category_id'] for c in cats]}")
            else:
                items = data.get("items", [])
                print(f"  {fname} — {len(items)} items")
                for item in items[:3]:
                    print(f"    {item.get('destination_code') or item.get('destination')} "
                          f"{item.get('price')} {item.get('currency')} "
                          f"dep:{item.get('departure_date')}")
                if len(items) > 3:
                    print(f"    ... and {len(items) - 3} more")
    else:
        print("  (no output/deals/ directory found)")