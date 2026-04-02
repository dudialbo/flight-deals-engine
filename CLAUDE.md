# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Setup:**
```bash
python -m venv venv && source venv/bin/activate
pip install -e .[dev]
```

**Testing:**
```bash
pytest                        # all tests
pytest tests/unit/test_foo.py # single test file
pytest --cov                  # with coverage
```

**Linting & type checking:**
```bash
ruff check src/ tests/
mypy src/
```

**Local job execution:**
```bash
python scripts/run_local_hot_deals.py   # runs all categories, writes to output/deals/
python scripts/run_local_refresh.py     # runs calendar prices refresh
```

**Deploy** (requires `SEARCH_BACKEND_BASE_URL` env var):
```bash
./scripts/deploy.sh
```
Builds a Docker image for `linux/amd64`, pushes to ECR, then runs `terraform apply`.

## Architecture

This is a Python background-job engine that fetches flight deals from a search backend and publishes results to S3 for a trip-planner frontend (Amiluna). It runs on AWS Lambda, triggered by EventBridge every 6 hours.

### Layer structure (hexagonal)

```
entrypoints/      ← Lambda handler — routes jobType to a job
jobs/             ← Job orchestration (refresh_deal_categories, refresh_calendar_prices)
application/      ← Service classes, category registry, deal refresh service
domain/           ← Pure business logic: models, interfaces, ranker, filters
adapters/         ← External I/O: search backend HTTP client, storage writers
config/           ← Pydantic settings loaded from environment
```

### Key flows

**Deal Categories job** (`jobs/refresh_deal_categories.py`) — primary job:
- Loads all category configs from `application/category_registry.py`
- For each category: fetches flights, filters, selects, ranks, validates, writes `deals/{category_id}.json`
- Writes `deals/manifest.json` with operational status for all categories
- `jobs/refresh_hot_deals.py` is a thin wrapper that delegates here (kept for EventBridge backward compatibility)

**Calendar Prices job** (`jobs/refresh_calendar_prices.py`):
- Generates cheapest-price-per-day snapshots for calendar views

### Adding a category

Add a `DealCategoryConfig` entry to `application/category_registry.py`. No other code changes needed. Fields:

| Field | Purpose |
|---|---|
| `selection_mode` | `cheapest_per_destination` (one pick per dest) or `best_overall` (global top-N) |
| `ranking_mode` | `price` (cheapest first) or `weekend` (stops → price → date) |
| `departure_days` | Python `weekday()` integers to restrict departure day (0=Mon … 6=Sun) |
| `return_days` | Same, for return day |
| `departure_months` | Month integers (1–12) to restrict to seasonal windows |
| `price_max` | Hard price ceiling (Decimal) |
| `max_stops` | Max stops per direction (None = no limit; 1 = at most 1 stop each way) |
| `layover_filter` | When True, rejects flights where layover > 50% of flying time on any leg |

Add any new IATA airport codes to `DESTINATION_NAMES` in `application/deal_refresh_service.py` so `destination_name` is populated correctly. The dict should use **airport codes** as keys (e.g. `"MXP"`, `"JFK"`), not city codes. The backend text name (`destination` field on the leg) is used as a fallback when a code is missing from the dict.

### Storage adapter factory

Four implementations behind a `StorageWriter` protocol: `s3`, `json` (local file under `output/deals/`), `in_memory` (tests), `null` (no-op). Selected via `STORAGE_ADAPTER` env var. Factory in `adapters/storage/factory.py`.

### Search backend adapter

`adapters/search_backend/client.py` wraps an HTTP API at `SEARCH_BACKEND_BASE_URL`.

**Rate limiting:** The client retries on HTTP 429 with exponential backoff (`SEARCH_BACKEND_MAX_RETRIES`, `SEARCH_BACKEND_RETRY_BACKOFF_SECONDS`). It respects the `Retry-After` header when present. After retries are exhausted it raises `RateLimitError`. The service catches this per destination — the affected destination is skipped and processing continues. Categories that had at least one destination skipped are written with `status: "partial"` and a `destinations_skipped` count in the manifest. Per-destination call throttling is configured via `SEARCH_BACKEND_REQUEST_DELAY_SECONDS`.

**Response normalisation** (`adapters/response_normalizer.py`):
- `destination_code` = airport code (`destinationCode` field), city code only as fallback
- `stops` = `max(outbound.stops, return.stops)` — represents worst leg; so `max_stops=1` means ≤1 stop per direction and `direct_only` rejects if either direction has any stop
- Layover quality is computed from `segments[].duration_seconds` and `layovers[].duration` on each leg; the leg with the worst layover/flight ratio is stored in `total_duration_minutes` / `layover_duration_minutes` on `FlightOption`

### Domain models

- `DealCategoryConfig` — category search parameters and filtering rules
- `DealItem` — a single ranked deal (output shape: `destination_code`, `destination_name`, `price`, `nights`, `direct`, `stops`, etc.)
- `CategoryPayload` — envelope written per category: `{ category: CategoryMeta, items: [DealItem] }`
- `ManifestPayload` — operational manifest: `{ generated_at, categories: [{ category_id, item_count, generated_at, status }] }`
- `FlightOption` — normalised search result; `destination_name` carries the backend's text city name as a fallback for the `DESTINATION_NAMES` lookup
- `CalendarPriceSnapshot` — cheapest price per day for calendar display

### Infrastructure (Terraform in `infra/`)

- Lambda with 256 MB / 300s timeout, Docker image deployed via ECR
- EventBridge rule sends `{"jobType": "refresh_hot_deals"}` every 6 hours
- S3 bucket `flight-deals-data-{environment}` (public access blocked)
- IAM role with CloudWatch Logs + S3 PutObject/GetObject

## Environment variables

Key vars (see `.env.example` for the full list):

| Variable | Default | Purpose |
|---|---|---|
| `SEARCH_BACKEND_BASE_URL` | required | Search API base URL |
| `STORAGE_ADAPTER` | `null` | `s3`, `json`, `in_memory`, or `null` |
| `S3_BUCKET_NAME` | — | Required when `STORAGE_ADAPTER=s3` |
| `DEFAULT_ORIGIN` | `TLV` | Origin airport code |
| `DEFAULT_CURRENCY` | `USD` | Currency for all searches |
| `HOT_DEALS_DESTINATIONS` | (13 destinations) | Comma-separated IATA codes for hot_deals category |
| `HOT_DEALS_SEARCH_HORIZON_DAYS` | `90` | Days ahead to search for hot_deals |
| `HOT_DEALS_NIGHTS_MIN/MAX` | `4`/`5` | Trip length for hot_deals |
| `HOT_DEALS_DIRECT_ONLY` | `true` | Direct flights only for hot_deals |
| `SEARCH_BACKEND_REQUEST_DELAY_SECONDS` | `0.3` | Throttle between per-destination calls |
| `SEARCH_BACKEND_MAX_RETRIES` | `3` | Retry attempts on HTTP 429 |
| `SEARCH_BACKEND_RETRY_BACKOFF_SECONDS` | `1.0` | Base backoff; doubles each attempt |