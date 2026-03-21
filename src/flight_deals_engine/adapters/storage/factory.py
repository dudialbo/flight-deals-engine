from typing import Protocol, Sequence

from flight_deals_engine.adapters.storage.json_file_writer import JsonFileStorageWriter
from flight_deals_engine.adapters.storage.s3_writer import S3StorageWriter
from flight_deals_engine.domain.models import CalendarPriceSnapshot, HotDealCandidate
from flight_deals_engine.adapters.storage.null_writer import NullStorageWriter
from flight_deals_engine.adapters.storage.in_memory_storage_writer import InMemoryStorageWriter


class StorageWriter(Protocol):
    def write_calendar_snapshots(self, items: Sequence[CalendarPriceSnapshot]) -> None: ...
    def write_hot_deals(self, items: Sequence[HotDealCandidate]) -> None: ...


def get_storage_writer(adapter_type: str, bucket_name: str | None = None) -> StorageWriter:
    if adapter_type == "in_memory":
        return InMemoryStorageWriter()

    if adapter_type == "json":
        return JsonFileStorageWriter()

    if adapter_type == "s3":
        if not bucket_name:
            raise ValueError("S3_BUCKET_NAME must be configured when using 's3' adapter")
        return S3StorageWriter(bucket_name=bucket_name)

    # Default to null
    return NullStorageWriter()
