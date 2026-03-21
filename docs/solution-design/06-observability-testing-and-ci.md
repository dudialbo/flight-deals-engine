# 06 — Observability, Testing, and CI

## Observability

Phase 1 should start with structured logs.

Each job run should log:

- job name
- run id
- targets planned
- backend calls attempted
- successful results
- records written
- failures
- duration

Metrics can be added after the first vertical slice, but code should be organized so metrics hooks are easy to add.

## Testing strategy

### Unit tests
- planner rules
- normalizer logic
- cheapest selection behavior
- adapter payload parsing

### Integration tests
- job orchestration with fake backend client
- storage writer interactions
- failure-path behavior

## CI baseline

Recommended initial checks:

- Ruff
- mypy
- pytest

Keep CI lean until the first working flow exists.
