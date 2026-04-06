# CLAUDE.md — Flight Deals Engine

AI assistant guide for the `flight-deals-engine` repository.

---

## What This Repo Does

Background async job engine for refreshing flight pricing data. Two jobs run on AWS Lambda:

1. **`refresh_hot_deals`** — Finds cheapest round-trips to 8–13 configured destinations, ranks them, and persists to S3. Runs every 6 hours via EventBridge.
2. **`refresh_calendar_prices`** — Generates monthly price snapshots for calendar/discovery flows.

This repo does **not** expose user-facing APIs. It calls an existing internal search backend and writes output to S3.

---

## Architecture: Clean/Hexagonal

```
entrypoints/ → application/ → domain/
                ↓
            adapters/  (search backend, storage)
```

| Layer | Path | Purpose |
|---|---|---|
| Domain | `src/flight_deals_engine/domain/` | Core models, interfaces (Protocols), scoring, selection |
| Application | `src/flight_deals_engine/application/` | Orchestration services, planners, commands |
| Adapters | `src/flight_deals_engine/adapters/` | HTTP client for search backend, storage writers |
| Jobs | `src/flight_deals_engine/jobs/` | Job runners wiring application services together |
| Entrypoints | `src/flight_deals_engine/entrypoints/` | Lambda handler, event parsing |
| Config | `src/flight_deals_engine/config/settings.py` | `pydantic-settings` loaded from env |

**Key rule**: inner layers never import from outer layers. Domain has no knowledge of adapters or entrypoints.

---

## Technology Stack

- **Python 3.11+**
- **Pydantic v2** — all data models and settings
- **httpx** — async-capable HTTP client for search backend calls
- **boto3** — AWS S3 integration
- **pytest + pytest-cov** — testing
- **mypy (strict)** — type checking
- **ruff** — linting (100-char line limit)
- **Terraform** — AWS infrastructure (Lambda, EventBridge, S3, IAM)
- **Docker** — Lambda-compatible image via `public.ecr.aws/lambda/python:3.13`

---

## Local Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

# Copy and configure environment
cp .env.example .env
# Edit .env with your values (especially SEARCH_BACKEND_BASE_URL)

# Run locally
python scripts/run_local_hot_deals.py
python scripts/run_local_refresh.py
```

---

## Running Tests and Linters

```bash
# All tests
pytest

# With coverage
pytest --cov

# Verbose
pytest -v

# Type checking
mypy src/

# Linting
ruff check src/ tests/
```

All four must pass before committing. There is no CI config file visible yet — run these manually.

---

## Configuration (`config/settings.py`)

Settings are loaded via `pydantic-settings` from environment variables or a `.env` file. Key settings:

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `dev` | Environment name |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `SEARCH_BACKEND_BASE_URL` | — | Internal search backend URL (required) |
| `SEARCH_BACKEND_TIMEOUT_SECONDS` | `20` | HTTP timeout |
| `DEFAULT_CURRENCY` | `USD` | Output currency |
| `DEFAULT_ORIGIN` | `TLV` | Departure airport IATA code |
| `MONTHS_AHEAD` | `6` | Search horizon in months |
| `HOT_DEALS_LIMIT` | `100` | Max deals to return |
| `STORAGE_ADAPTER` | `null` | One of: `null`, `in_memory`, `json`, `s3`, `dynamodb` |

In tests, always construct settings with `_env_file=None` to prevent picking up real `.env` files:
```python
settings = Settings(_env_file=None, SEARCH_BACKEND_BASE_URL="http://test")
```

---

## Key Files to Know

| File | Purpose |
|---|---|
| `entrypoints/lambda_handler.py` | Lambda entry, routes `jobType` to job runners |
| `jobs/refresh_hot_deals.py` | Main job: fetch → select → rank → persist |
| `jobs/refresh_calendar_prices.py` | Calendar job: plan → fetch → snapshot → persist |
| `application/hot_deals_service.py` | `HotDealsRefreshService` — core orchestration |
| `application/planner.py` | `RefreshPlanner` — generates monthly search targets |
| `domain/hot_deal_scorer.py` | `HotDealScorer` — ranking: price → date → destination |
| `domain/models.py` | `RefreshTarget`, `FlightOption`, `HotDealCandidate`, `CalendarPriceSnapshot` |
| `domain/interfaces.py` | `Protocol` definitions for `SearchBackendClient`, writers |
| `adapters/search_backend/client.py` | `SearchBackendHttpClient` — POST `/search/flights` |
| `adapters/storage/factory.py` | Selects storage writer from `STORAGE_ADAPTER` setting |

---

## Storage Adapters

| Adapter | Use Case |
|---|---|
| `null` | Default, discards output (safe for local testing) |
| `in_memory` | Integration tests |
| `json` | Local file output |
| `s3` | Production (Lambda) |

All adapters implement the `PriceSnapshotWriter` / `HotDealsWriter` protocols from `domain/interfaces.py`.

To add a new writer: implement the protocol, add a case in `adapters/storage/factory.py`.

---

## Lambda Event Format

```json
{
  "jobType": "refresh_hot_deals"
}
```

or

```json
{
  "jobType": "refresh_calendar_prices",
  "originIata": "TLV",
  "destinationIata": "BCN",
  "year": 2026,
  "month": 4
}
```

Handled in `entrypoints/lambda_handler.py` via command models in `entrypoints/models.py`.

---

## Code Conventions

- **Type hints everywhere** — mypy strict mode is enforced
- **Pydantic for all data** — no raw dicts crossing layer boundaries
- **`Decimal` for money** — never `float` for monetary values
- **ISO strings for dates/times** — `"2026-04-06"`, `"2026-04-06T10:00:00Z"`
- **Error isolation in jobs** — jobs catch per-destination errors, log, and continue
- **No direct `print()`** — use `logging` via `observability/logging.py`
- **Class naming** — descriptive suffixes: `...Service`, `...Client`, `...Writer`, `...Scorer`
- **Private methods** — underscore prefix (`_fetch_candidates`)
- **No cross-layer imports** — domain must not import from adapters or entrypoints

---

## Testing Conventions

- Unit tests live in `tests/unit/`, integration tests in `tests/integration/`
- Mock external dependencies with `unittest.mock`
- Use `httpx` response mocking for HTTP adapter tests
- Integration tests use `in_memory` storage adapter to verify full flows
- Fixture pattern: build `Settings(_env_file=None, ...)` then wire dependencies manually
- Test files mirror source structure: `test_<module_name>.py`

---

## Infrastructure (Terraform)

Located in `infra/`. Key resources:

- **Lambda** (`lambda.tf`): 256 MB, 5 min timeout, Docker image from ECR
- **EventBridge** (`event_bridge.tf`): Triggers `refresh_hot_deals` every 6 hours
- **S3** (`s3.tf`): Output bucket; writes `hot_deals.json` and `calendar_prices.json`
- **IAM** (`iam.tf`): Lambda execution role with S3 `PutObject` permission

---

## What's Intentionally Out of Scope

- No hotel/transport data (flights only in phase 1)
- No user-facing API — this is a background worker only
- No direct integration with flight providers (uses internal search backend)
- No round-trip price breakdown by leg

---

## Documentation

Detailed design docs are in `docs/solution-design/`:

1. `01-scope-and-boundaries.md` — What this repo is/isn't
2. `02-runtime-and-job-model.md` — Lambda design and event format
3. `03-search-backend-contract.md` — Backend API contract
4. `04-domain-model-and-normalization.md` — Internal models
5. `05-storage-abstraction.md` — Storage adapter pattern
6. `06-observability-testing-and-ci.md` — Testing and observability practices
