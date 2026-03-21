# 02 — Runtime and Job Model

## Runtime choice

Use AWS Lambda in phase 1.

## Why Lambda now

- no traffic pressure yet
- simple scheduled execution via EventBridge
- cheap operationally for low-volume jobs
- good enough for modest route/date refresh batches

## Runtime design rule

Business logic must not depend on Lambda details.

The Lambda handler should only:

- read the incoming event
- load configuration
- select the job runner
- return a summary result

## Initial job set

### `refresh_calendar_prices`
First real implementation target.

Purpose:
- refresh cheapest known flight price snapshots for selected routes/month windows

Consumers later:
- frontend calendar widgets
- inspiration cards
- planner precomputed hints

### `refresh_hot_deals`
Scaffold only in phase 1.

Purpose later:
- build ranked deal candidates for hot deals feeds and marketing channels

## Event format

Recommended event shape:

```json
{
  "jobType": "refresh_calendar_prices",
  "runId": "optional-external-id",
  "scope": {
    "origins": ["TLV"],
    "destinations": ["LON", "ROM", "PAR"],
    "monthsAhead": 6
  }
}
```

The handler may also support defaults when `scope` is omitted.

## Future evolution

If Lambda duration or concurrency becomes limiting, the same job modules should be callable from:

- a CLI runner
- ECS/Fargate jobs
- Step Functions orchestrations
