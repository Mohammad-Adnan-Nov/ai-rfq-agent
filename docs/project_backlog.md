# Project Backlog

## Current Phase

Phase 0 - Project setup, governance, and architecture lock.

## Phase 0 Status

Completed:

- Git repository initialized
- GitHub remote connected
- Project skeleton created
- README created
- .gitignore created
- .env.example created
- requirements.txt created
- requirements-dev.txt created
- pyproject.toml created
- Documentation folder created
- ADR files created
- Initial unit tests created
- GitHub Actions CI created
- CI passing

## Critical Governance Rules

1. The AI must never invent part numbers.
2. SQL Server is the source of truth.
3. Qdrant is only for semantic retrieval.
4. OpenAI only extracts RFQ meaning and validates retrieved candidates.
5. Raw Excel pricebooks must not be committed to GitHub.
6. Customer RFQs must not be committed to GitHub.
7. Secrets must stay in .env, never in code.
8. The LLM must not generate SQL.
9. The system must preserve source traceability for every recommended candidate.
10. Sales users must review results before quoting.

## Current Approved Scope

Included:

- RFQ text understanding
- approved Fishing Tool part-number retrieval
- source traceability
- search_text generation
- SQL-ready pricebook ingestion
- candidate ranking
- later LLM validation of retrieved candidates only

Excluded for now:

- auto-quoting
- JDE integration
- sales order creation
- Outlook automation
- Teams automation
- Power Automate workflow
- pricing automation
- customer auto-replies

## Open Decisions

These do not block local development, but must be answered before pilot rollout:

1. Which SQL Server environment will be used?
2. Is OpenAI approved for real RFQ text?
3. Which workbook version is the approved source?
4. Who will review the golden RFQ dataset?
5. What authentication method will be used for pilot users?
6. Will Qdrant and MLflow be self-hosted or managed?

## Next Phase

Phase 1 - Pricebook Data Foundation.

## Phase 1 First Goal

Create a workbook profiling script.

The script should inspect the Excel pricebook and produce a workbook profile report.

The first script will be:

scripts/profile_workbook.py

The first ingestion module will be:

src/rfq_agent/ingestion/workbook_reader.py

## Phase 1 Will Not Yet Include

- SQL Server loading
- Qdrant indexing
- OpenAI calls
- LangGraph workflow
- FastAPI
- Streamlit
- MLflow

Those come later.

## Phase 1 First Output

The first output should be a local report such as:

data/processed/workbook_profile.json

This report should summarize:

- workbook file name
- sheet names
- visible sheet count
- hidden sheet count
- row and column counts per sheet
- whether a Data sheet exists
- detected headers in the Data sheet


### Phase 1 SQL foundation completed:

- Phase 1 DDL executed locally in AI_RFQ_AGENT_DEV.
- SQL pricebook loader created.
- Canonical pricebook item records loaded into rfq schema.
- 12,092 pricebook item contexts loaded.
- 11,138 valid candidates loaded.
- 954 invalid candidates retained for audit but excluded from search index.
- SQL post-load validation script added and passing.
