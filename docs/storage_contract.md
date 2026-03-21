# Storage Contract

This document defines the data models and storage requirements for the Flight Deals Engine.

## Storage Strategy

The engine produces two main types of data:
1. **Calendar Price Snapshots**: The cheapest flight price found for a given route and month.
2. **Hot Deals**: Specific flight options identified as high-value deals.

Recommended storage: **DynamoDB** (for fast read/write access by frontend/API) or **S3** (for batched data lake access).

## Calendar Price Snapshots

This data powers the "Best Price Calendar" feature.

### Schema

| Field | Type | Description | Example |
|---|---|---|---|
| `pk` | String | Partition Key: `CALENDAR#{origin}#{destination}` | `CALENDAR#TLV#LON` |
| `sk` | String | Sort Key: `MONTH#{YYYY-MM}` | `MONTH#2023-10` |
| `price` | Number | The cheapest price found | `150.00` |
| `currency` | String | Currency code | `USD` |
| `updated_at` | String | ISO 8601 Timestamp of discovery | `2023-10-01T12:00:00Z` |
| `ttl` | Number | Time-to-live timestamp (optional, e.g., 7 days) | `1696766400` |

### Access Patterns
- **Get monthly price**: `GetItem(pk="CALENDAR#TLV#LON", sk="MONTH#2023-10")`
- **Get year prices**: `Query(pk="CALENDAR#TLV#LON", sk_begins_with="MONTH#2023")`

## Hot Deals

This data powers the "Hot Deals" feed.

### Schema

| Field | Type | Description | Example |
|---|---|---|---|
| `pk` | String | Partition Key: `DEAL#{origin}` | `DEAL#TLV` |
| `sk` | String | Sort Key: `SCORE#{score}#{destination}#{date}` | `SCORE#8.5#LON#2023-10-15` |
| `deal_id` | String | Unique deal identifier | `uuid` |
| `destination` | String | Destination code | `LON` |
| `price` | Number | Deal price | `99.00` |
| `score` | Number | Deal quality score (higher is better) | `8.5` |
| `departure_date` | String | Flight departure date | `2023-10-15` |
| `return_date` | String | Return date (optional) | `2023-10-22` |
| `deep_link` | String | Booking URL | `https://...` |
| `ttl` | Number | Expiration timestamp (e.g., flight departure or 24h) | `1696204800` |

### Access Patterns
- **Get top deals from origin**: `Query(pk="DEAL#TLV", scan_index_forward=False, limit=10)` (Reverse sort by score)

## Infrastructure Requirements

- **DynamoDB Table**: `FlightDeals` (Single Table Design recommended).
- **TTL Attribute**: `ttl` (enabled on table).
- **Throughput**: On-demand capacity mode recommended for batch jobs.
