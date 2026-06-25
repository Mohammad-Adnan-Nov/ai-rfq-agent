# ADR 0003: Use Qdrant for Semantic Retrieval Only

## Status

Accepted.

## Decision

Qdrant will be used only as a semantic retrieval index.

## Reason

Semantic search helps when RFQ wording is vague, abbreviated, or different from pricebook descriptions.

## Consequences

- Qdrant is not the source of truth.
- Qdrant stores vectors and minimal metadata only.
- Full item details must be fetched from SQL Server.
- Qdrant should be added only after SQL retrieval baseline is working.
