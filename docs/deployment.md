# Deployment

## Current Deployment Status

Not started.

## Development Target

Local development should use:

- Python virtual environment
- local project folder
- local raw workbook in data/raw
- GitHub repository
- later Docker Compose for Qdrant and MLflow

## Pilot Target

Pilot deployment may use:

- FastAPI backend
- Streamlit UI
- SQL Server
- Qdrant
- MLflow
- Docker Compose

## Important Deployment Rule

Do not deploy to sales users until:

- pricebook ingestion is validated
- no-invention guardrail is tested
- data policy is confirmed
- raw RFQ logging is reviewed
- authentication approach is decided
