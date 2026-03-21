# 05 — Storage Abstraction

## Constraint

This repo must not provision or hard-code production storage infrastructure yet.

## Design decision

Storage is represented by interfaces plus lightweight adapters.

## Why

- database/cache infra will live in a dedicated infra repo
- refresh logic should be testable before infra is finalized
- we can decide later between DynamoDB, S3 JSON, Redis, or a mixed approach

## Required write paths

### Calendar snapshots
A batch write interface for route/month snapshot outputs.

### Hot deals
A batch write interface for ranked deals.

## Initial adapters

- `NullStorageWriter` for bootstrap wiring
- recommended next: `InMemoryStorageWriter` for tests and local simulation

## Future compatible targets

The abstraction should support later implementations such as:

- DynamoDB writer
- S3 snapshot exporter
- Redis cache materializer

The application layer should not care which one is active.
