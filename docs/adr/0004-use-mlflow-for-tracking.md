# ADR 0004: Use MLflow for Tracking and Evaluation

## Status

Accepted.

## Decision

MLflow will be used for tracking runs, evaluations, model versions, prompt versions, and retrieval versions.

## Reason

The project needs measurable, repeatable evaluation without relying only on manual demos.

## Consequences

- MLflow is not a business database.
- MLflow must not store secrets.
- Raw customer RFQ text should not be logged until data policy is approved.
- Metrics such as Recall at 5 and no-invention rate should be tracked.
