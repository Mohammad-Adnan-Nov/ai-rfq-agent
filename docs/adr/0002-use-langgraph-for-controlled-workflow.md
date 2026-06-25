# ADR 0002: Use LangGraph for Controlled Workflow

## Status

Accepted.

## Decision

LangGraph will be used later to orchestrate the RFQ matching workflow.

## Reason

The RFQ Agent needs predictable steps, not an unrestricted autonomous agent.

The workflow should be:

parse
-> normalize
-> retrieve
-> rank
-> validate
-> guardrail
-> format response

## Consequences

- LangGraph will not be used during Excel ingestion.
- LangGraph starts only after SQL retrieval baseline exists.
- Each workflow node must be testable.
