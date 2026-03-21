# 04 — Domain Model and Normalization

## Goal

Define stable internal models that represent refresh outputs independently of backend/provider payload shape.

## Core models

### `RefreshTarget`
Represents a single background search task.

### `FlightOption`
Represents one normalized flight result returned by the internal backend.

### `CalendarPriceSnapshot`
Represents the cheapest known price for a route-month combination.

### `HotDealCandidate`
Represents a future ranked output for hot deals.

## Normalization rules

Normalize at the boundary:

- dates into typed date values
- timestamps in UTC
- price into Decimal
- currency into a stable uppercase code
- route/origin/destination into canonical codes used by the backend

## Why this matters

Without normalization, the refresh logic becomes coupled to backend response details and harder to test.

## Phase 1 decision

Keep models intentionally small.

Do not add fields until a job truly needs them.
