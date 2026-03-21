from flight_deals_engine.application.normalizer import FlightNormalizer
from flight_deals_engine.domain.interfaces import PriceSnapshotWriter, SearchBackendClient
from flight_deals_engine.domain.models import CalendarPriceSnapshot, RefreshTarget


class CalendarRefreshService:
    def __init__(
        self,
        search_client: SearchBackendClient,
        snapshot_writer: PriceSnapshotWriter,
        normalizer: FlightNormalizer,
    ) -> None:
        self._search_client = search_client
        self._snapshot_writer = snapshot_writer
        self._normalizer = normalizer

    def refresh(self, targets: list[RefreshTarget], source_job: str, month: str) -> list[CalendarPriceSnapshot]:
        snapshots: list[CalendarPriceSnapshot] = []
        for target in targets:
            results = self._search_client.search_flights(target)
            if not results:
                continue
            cheapest = min(results, key=lambda item: item.price)
            snapshots.append(self._normalizer.to_calendar_snapshot(source_job=source_job, month=month, flight=cheapest))
        self._snapshot_writer.write_calendar_snapshots(snapshots)
        return snapshots
