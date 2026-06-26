# AI RFQ Agent

AI-assisted RFQ retrieval and Fishing Tool part-number matching system for NOV Downhole / Fishing Tools.

---

## Overview

The AI RFQ Agent is designed to help NOV sales and applications users identify approved Fishing Tool part numbers from unstructured and often incomplete RFQ (Request for Quotation) text.

The system combines deterministic retrieval, semantic search, and AI-assisted validation to improve search accuracy while maintaining strict governance and traceability requirements.

Typical RFQs received from customers may contain:

```text

Single Pawl Spacer F/- 5 7/8" OD Outside Cutter

Guide F/- 5 7/8" OD Outside Cutter

8 1/8" OD Oversize Guide F/- 5 7/8" OD Outside Cutter

(Bowen CA# 47264)


GRAPPLE, SPIRAL CA

CNTL, SPIRAL GRAPPLE CA

PACKER, TYPE A CA
```

The agent extracts product intent, retrieves matching candidates, ranks results, and provides transparent recommendations for human review.

---

## Business Objective

Sales teams frequently receive RFQs containing:

- Incomplete product descriptions
- Legacy Bowen references
- Customer terminology
- Typographical errors
- Mixed formatting
- Multiple items in a single request

Finding the correct approved part number manually can be time-consuming and error-prone.

The AI RFQ Agent aims to:

- Reduce RFQ processing time
- Improve part-number search accuracy
- Preserve engineering-approved part governance
- Provide explainable retrieval results
- Support human decision-making rather than replace it

---

## Governance Principles

### Critical Rule

**The AI must never invent part numbers.**

All approved part numbers must originate from the authoritative company data source.

### Approved Responsibilities

OpenAI models may be used for:

- RFQ meaning extraction
- Attribute extraction
- Candidate validation
- Similarity reasoning
- Embedding generation

### Prohibited Responsibilities

OpenAI models must **not**:

- Generate new part numbers
- Modify approved part numbers
- Act as the source of truth
- Override governed data

---

## Source of Truth

### SQL Server

SQL Server is the authoritative source for:

- Approved part numbers
- Product descriptions
- Product attributes
- Traceability fields
- Source records

### Qdrant

Qdrant is used only for:

- Semantic search
- Vector similarity retrieval

Qdrant is **not** the source of truth.

### MLflow

MLflow is used for:

- Experiment tracking
- Prompt versioning
- Model versioning
- Evaluation runs
- Governance auditing

MLflow is **not** a production data source.

---

## Core Workflow

```text

RFQ Text

    │

    ▼

RFQ Meaning Extraction

    │

    ▼

Deterministic Normalization

    │

    ▼

SQL Retrieval

    │

    ▼

Semantic Retrieval (Qdrant)

    │

    ▼

Candidate Ranking

    │

    ▼

AI Candidate Validation

    │

    ▼

Output Guardrail

    │

    ▼

Human Review
```

---

## Target Architecture

```text

Streamlit UI

    │

    ▼

FastAPI Backend

    │

    ▼

LangGraph Workflow

    │

    ├── RFQ Extraction

    ├── Deterministic Normalization

    ├── SQL Retrieval

    ├── Qdrant Semantic Retrieval

    ├── Candidate Ranking

    ├── Candidate Validation

    └── Output Guardrails

    │

    ▼

SQL Server (Source of Truth)


Supporting Services

    ├── Qdrant

    └── MLflow
```

---

## Project Scope

### In Scope

- RFQ retrieval
- Product matching
- Fishing Tool part-number search
- Pricebook ingestion
- Candidate ranking
- Source traceability
- Human review workflows
- Evaluation framework
- Governance controls

### Out of Scope (Current Phase)

The following capabilities are intentionally excluded from the current project scope:

- Automated quoting
- JDE integration
- Sales order creation
- Outlook automation
- Microsoft Teams automation
- Power Automate workflows
- Customer auto-replies
- Pricing automation

---

## Development Roadmap

### Phase 0 — Project Setup & Governance

- Repository setup
- Coding standards
- Data governance
- Documentation
- Development environment

### Phase 1 — Data Foundation

- Pricebook ingestion
- Data cleaning
- Product normalization
- Search text generation
- SQL-ready datasets
- Data quality reporting

### Phase 2 — SQL Retrieval Engine

- Exact retrieval
- Attribute filtering
- Deterministic search

### Phase 3 — Qdrant Semantic Search

- Embedding generation
- Vector indexing
- Semantic retrieval

### Phase 4 — LangGraph Workflow

- RFQ extraction workflow
- Retrieval orchestration
- Validation flow

### Phase 5 — FastAPI Backend

- API endpoints
- Service layer
- Authentication

### Phase 6 — Streamlit Pilot UI

- Search interface
- Candidate review
- Traceability views

### Phase 7 — Evaluation Framework

- Ground-truth datasets
- Retrieval metrics
- Benchmarking

### Phase 8 — Docker Deployment

- Containerization
- Environment management
- Deployment automation

---

## Current Phase

### Phase 0 — Project Setup & Governance

The project is currently focused on establishing a strong foundation.

**Do not begin implementation of:**

- LangGraph workflows
- OpenAI retrieval pipelines
- Qdrant indexing
- FastAPI services
- Streamlit applications

until the data foundation is complete and validated.

---

## First Implementation Milestone

The most important milestone is the creation of a trusted data foundation:

```text

Excel Pricebook

     │

     ▼

Data Cleaning

     │

     ▼

Structured SQL-Ready Dataset

     │

     ├── Product Records

     ├── Source Traceability

     ├── Search Text

     └── Quality Metrics

     │

     ▼

Data Quality Report
```

### Deliverables

- Clean structured dataset
- Standardized product descriptions
- Searchable text fields
- Traceability metadata
- Data quality report
- SQL-ready output tables

All downstream AI and retrieval capabilities depend on the quality of this foundation.

---

## Repository Structure

```text

ai-rfq-agent/

│

├── data/

│   ├── raw/

│   ├── processed/

│   └── curated/

│

├── notebooks/

│

├── src/

│   └── rfq_agent/

│

├── tests/

│

├── docs/

│

├── scripts/

│

├── deployment/

│

├── alembic/

│

├── README.md

├── requirements.txt

├── requirements-dev.txt

├── pyproject.toml

├── .env.example

└── .gitignore
```

---

## Local Development Setup

### 1. Create Virtual Environment

```bash

python -m venv .venv
```

### 2. Activate Environment

PowerShell:

```powershell

.\.venv\Scripts\Activate.ps1
```

### 3. Upgrade Pip

```bash

python -m pip install --upgrade pip
```

### 4. Install Dependencies

```bash

pip install -r requirements.txt

pip install -r requirements-dev.txt
```

---

## Testing

Run automated tests:

```bash

pytest
```

---

## Code Quality

Run linting:

```bash

ruff check .
```

Optional formatting:

```bash

ruff format .
```

---

## Data Security

The repository must never contain sensitive business data.

### Do Not Commit

- Raw pricebooks
- Customer RFQs
- `.env`
- OpenAI API keys
- SQL Server credentials
- Qdrant credentials
- MLflow credentials

### Raw Data Location

Local-only source files may be stored in:

```text

data/raw/
```

This directory must remain excluded from Git tracking.

---

## Traceability Requirements

Every candidate recommendation must be traceable back to its original source record.

Minimum traceability fields include:

- Source workbook
- Source sheet
- Source row
- Original description
- Approved part number
- Load timestamp
- Data version

No recommendation should be returned without an auditable source.

---

## Success Criteria

The project is considered successful when it can:

1. Accept messy RFQ text.
2. Extract product intent reliably.
3. Retrieve approved candidate part numbers.
4. Rank candidates transparently.
5. Maintain full source traceability.
6. Prevent hallucinated part numbers.
7. Keep SQL Server as the single source of truth.
8. Support efficient human review.

## Governance Rules

### No-Invention Rule

The AI RFQ Agent must never invent part numbers.

### Source of Truth

SQL Server is the source of truth for all approved part numbers and business records.

Qdrant is only used for semantic retrieval and vector search.

The LLM may only recommend candidates retrieved from approved data sources.

---

## License

Internal NOV project. Confidential and intended for authorized business use only.
