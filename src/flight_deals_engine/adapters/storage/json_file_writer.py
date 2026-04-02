import json
import os
from typing import Any, Mapping, Sequence
from flight_deals_engine.domain.models import CalendarPriceSnapshot


class JsonFileStorageWriter:
    """
    Storage writer used for local debugging and quality verification.
    It writes the outputs to JSON files in a specified output directory.
    """
    def __init__(self, output_dir: str = "output") -> None:
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def write_calendar_snapshots(self, items: Sequence[CalendarPriceSnapshot]) -> None:
        file_path = os.path.join(self.output_dir, "calendar_prices.json")
        data = [item.model_dump(mode="json") for item in items]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(items)} calendar snapshots to {file_path}")

    def write_category(self, category_id: str, payload: Mapping[str, Any]) -> None:
        deals_dir = os.path.join(self.output_dir, "deals")
        os.makedirs(deals_dir, exist_ok=True)
        file_path = os.path.join(deals_dir, f"{category_id}.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(dict(payload), f, indent=2)
        print(f"Saved category {category_id} to {file_path}")

    def write_manifest(self, payload: Mapping[str, Any]) -> None:
        deals_dir = os.path.join(self.output_dir, "deals")
        os.makedirs(deals_dir, exist_ok=True)
        file_path = os.path.join(deals_dir, "manifest.json")
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(dict(payload), f, indent=2)
        print(f"Saved manifest to {file_path}")