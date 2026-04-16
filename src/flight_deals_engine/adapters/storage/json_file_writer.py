import json
import os
from typing import Sequence
from flight_deals_engine.domain.models import CalendarPriceSnapshot, HotDealCandidate

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
        # mode="json" ensures decimals and datetimes are serialized to JSON-safe formats
        data = [item.model_dump(mode="json") for item in items]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(items)} calendar snapshots to {file_path}")

    def write_hot_deals(self, items: Sequence[HotDealCandidate]) -> None:
        file_path = os.path.join(self.output_dir, "hot_deals.json")
        data = [item.model_dump(mode="json") for item in items]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(items)} hot deals to {file_path}")

    def write_last_minute_deals(self, items: Sequence[HotDealCandidate]) -> None:
        file_path = os.path.join(self.output_dir, "last_minute_deals.json")
        data = [item.model_dump(mode="json") for item in items]
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved {len(items)} last minute deals to {file_path}")
