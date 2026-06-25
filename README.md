# AI RFQ Agent

AI-assisted RFQ retrieval and Fishing Tool part-number matching system for NOV Downhole / Fishing Tools.

## Project Goal

The goal of this project is to help sales users identify approved Fishing Tool part numbers from messy RFQ text.

The system should support RFQ text such as:

`	ext
Single Pawl Spacer F/- 5 7/8" OD Outside Cutter
Guide F/- 5 7/8" OD Outside Cutter
8 1/8" OD Oversize guide F/- 5 7/8" OD outside cutter (Bowen CA# 47264)
GRAPPLE, SPIRAL CA
CNTL, SPIRAL GRAPPLE CA
PACKER, TYPE A CA

The system will extract RFQ meaning, retrieve approved candidates, rank them, and show traceable results to a sales user.

Critical Governance Rule

The AI must never invent part numbers.

Approved part numbers must come from SQL Server.

OpenAI may be used for:

RFQ meaning extraction
candidate validation
embeddings

OpenAI must not be used as the source of truth for part numbers.

Source of Truth

SQL Server is the source of truth.

Qdrant is only a semantic/vector retrieval index.

MLflow is only for tracking, evaluation, prompt versions, model versions, and governance.

Current Scope

Current scope:

RFQ retrieval
Fishing Tool part-number matching
pricebook ingestion
candidate ranking
source traceability
human review

Out of scope for now:

auto-quoting
JDE integration
sales order creation
Outlook automation
Teams automation
Power Automate workflow
customer auto-replies
pricing automation
Target Architecture
Streamlit UI
   -> FastAPI backend
   -> LangGraph workflow
      -> OpenAI RFQ extraction
      -> deterministic normalization
      -> SQL retrieval
      -> Qdrant semantic retrieval
      -> candidate ranking
      -> OpenAI candidate validation
      -> output guardrail
   -> SQL Server source of truth
   -> MLflow tracking
Development Phases
Phase 0: Project setup and governance
Phase 1: Pricebook data foundation
Phase 2: SQL retrieval engine
Phase 3: Qdrant semantic search
Phase 4: LangGraph RFQ workflow
Phase 5: FastAPI backend
Phase 6: Streamlit pilot UI
Phase 7: Evaluation framework
Phase 8: Docker deployment
Current Phase

Current phase:

Phase 0 - Project setup and governance

Do not start LangGraph, Qdrant, FastAPI, Streamlit, or OpenAI workflow until the data foundation is ready.

Local Setup

Create a Python virtual environment:

python -m venv .venv

Activate it:

.\.venv\Scripts\Activate.ps1

Upgrade pip:

python -m pip install --upgrade pip

Install dependencies:

pip install -r requirements.txt
pip install -r requirements-dev.txt
Data Safety

Do not commit raw pricebook files.

The workbook may be stored locally in:

data/raw/

But files inside data/raw/ are ignored by Git.

Do not commit:

Excel pricebooks
customer RFQs
.env
OpenAI API keys
SQL Server passwords
Qdrant API keys
MLflow credentials
Testing

Run tests with:

pytest

Run linting with:

ruff check .
Repository Structure
ai-rfq-agent/
+-- data/
+-- notebooks/
+-- src/rfq_agent/
+-- tests/
+-- docs/
+-- scripts/
+-- deployment/
+-- alembic/
+-- README.md
+-- requirements.txt
+-- requirements-dev.txt
+-- pyproject.toml
+-- .env.example
+-- .gitignore
First Implementation Milestone

The first real implementation milestone is:

Excel pricebook
-> clean structured SQL-ready dataset
-> source traceability
-> generated search_text
-> data quality report

Everything else depends on the quality of this foundation.
