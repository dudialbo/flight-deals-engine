# 03 — Search Backend Contract

## Design principle

This repo must call the existing internal search backend rather than talking directly to providers.

## Why

- search rules stay centralized
- affiliate/provider logic is not duplicated
- user searches and background refreshes can converge on the same behavior
- changing providers later should not require rewriting this repo

## Adapter responsibility

The search backend adapter owns:

- endpoint selection
- request payload construction
- authentication and headers
- timeout/retry policy
- response parsing and validation
- conversion into internal `FlightOption`

## Implemented Backend Contract

The refresh job uses the `POST /search/flights` endpoint to fetch flight options for date ranges.

### Endpoint

```http
POST /search/flights
```

### Request Payload

Example request body (snake_case):

```json
{
  "origin": "TLV",
  "destination": "LON",
  "date_from": "2026-06-01",
  "date_to": "2026-06-30",
  "return_from": "2026-06-04",  # derived from date_from + min_nights
  "return_to": "2026-07-07",    # derived from date_to + max_nights
  "nights_in_dst_from": 3,
  "nights_in_dst_to": 7,
  "passengers": 1,
  "limit": 100,
  "max_stopovers": 0            # if direct_only requested
}
```

### Response Payload

The backend returns a list of flight results with nested leg details.

```json
{
  "results": [
    {
      "outbound": {
        "id": "outbound_id",
        "airline": "British Airways",
        "flightNumber": "BA165",
        "originCode": "TLV",
        "destinationCode": "LHR",
        "departureDate": "2026-06-12"
      },
      "return": {  # Optional, null for one-way
        "id": "return_id",
        "airline": "British Airways",
        "flightNumber": "BA164",
        "originCode": "LHR",
        "destinationCode": "TLV",
        "departureDate": "2026-06-18"
      },
      "price": 219.99,
      "currency": "USD",
      "deep_link": "https://..."
    }
  ]
}
```

## Normalization

The adapter normalizes this structure into the internal `FlightOption` model:

- `origin` -> `outbound.originCode`
- `destination` -> `outbound.destinationCode`
- `departure_date` -> `outbound.departureDate`
- `return_date` -> `return.departureDate` (if present)
- `price` -> `price`
- `currency` -> `currency`
- `deeplink` -> `deep_link`
- `provider_name` -> `outbound.airline`

## Future Considerations

If additional fields (e.g., cabin class, baggage) are needed for filtering, update `RefreshTarget` and the request payload accordingly.
