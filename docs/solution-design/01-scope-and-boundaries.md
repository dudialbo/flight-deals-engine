# 01 — Scope and Boundaries

## Goal

Define exactly what this repository owns in phase 1.

## In scope

- scheduled flight refresh jobs
- calls to the existing internal search backend
- normalization into internal flight refresh models
- production of cached calendar-price and future hot-deal outputs
- reusable orchestration for later planner support

## Out of scope

- direct third-party provider access
- trip planner orchestration itself
- hotel and package search logic
- infrastructure provisioning for databases/cache
- user-facing synchronous APIs

## Boundary decision

The existing serving backend remains the execution layer for searches. This repo is a background data producer.

That means:

- search semantics remain centralized in the serving backend
- this repo focuses on refresh strategy and derived data generation
- future provider changes should ideally remain behind the serving backend contract

## Why this boundary is good

- fewer places to encode search logic
- easier to swap providers later
- less duplication between user-triggered search and scheduled refresh
- smaller blast radius while traffic is low
