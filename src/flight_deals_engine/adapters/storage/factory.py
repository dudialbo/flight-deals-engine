from typing import Protocol, Sequence

from flight_deals_engine.adapters.storage.json_file_writer import JsonFileStorageWriter
from flight_deals_engine.domain.models import CalendarPriceSnapshot, HotDealCandidate
from flight_deals_engine.adapters.storage.null_writer import NullStorageWriter
from flight_deals_engine.adapters.storage.in_memory_storage_writer import InMemoryStorageWriter


class StorageWriter(Protocol):
    def write_calendar_snapshots(self, items: Sequence[CalendarPriceSnapshot]) -> None: ...
    def write_hot_deals(self, items: Sequence[HotDealCandidate]) -> None: ...


def get_storage_writer(adapter_type: str) -> StorageWriter:
    if adapter_type == "in_memory":
        return InMemoryStorageWriter()

    if adapter_type == "json":
        return JsonFileStorageWriter()

    # Default to null
    return NullStorageWriter()
