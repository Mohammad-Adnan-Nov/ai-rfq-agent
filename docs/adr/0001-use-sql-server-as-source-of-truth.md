# ADR 0001: Use SQL Server as Source of Truth

## Status

Accepted.

## Decision

SQL Server will be the source of truth for approved Fishing Tool part numbers and structured pricebook records.

## Reason

Approved part data must be controlled, auditable, queryable, and traceable.

## Consequences

- The LLM cannot invent part numbers.
- Qdrant cannot be treated as source of truth.
- Search results must resolve back to SQL Server records.
- Final output must only show part numbers that exist in SQL Server.
