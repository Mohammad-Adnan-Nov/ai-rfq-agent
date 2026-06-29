# SQL Schema Draft

## Purpose

This document defines the SQL Server schema direction for the AI RFQ Agent pricebook data foundation.

The goal is to store approved Fishing Tool pricebook records in SQL Server so that SQL Server becomes the source of truth for:

- part-number retrieval
- source traceability
- assembly/component relationship lookup
- future synonym and alias matching
- future RFQ candidate evidence and feedback

This document is a schema design draft only. It does not create SQL tables yet.

---

## Current Phase

Current phase:

```text
Phase 1 - Pricebook Data Foundation
```

We are not yet connecting to SQL Server.

We are not yet building:

- Qdrant
- OpenAI workflow
- LangGraph
- FastAPI
- Streamlit
- MLflow tracking
- RFQ transaction tables

---

## Current Workbook Findings

The current extracted `Data` sheet preview shows:

| Metric | Value |
|---|---:|
| Item context rows | 12,092 |
| Valid candidate rows | 11,138 |
| Invalid candidate rows | 954 |
| Placeholder part-number rows | 924 |
| Blank-description invalid rows | 30 |
| Duplicate part-number contexts | 5,706 |

Important interpretation:

Duplicate part-number contexts are expected.

The same part number can appear in multiple sections, assemblies, or pricebook contexts. Therefore, the SQL design must separate:

```text
parts              = unique part numbers
pricebook_items    = part numbers in specific workbook/section/source contexts
```

---

## Core Design Principles

1. SQL Server is the source of truth.
2. Qdrant is only a semantic retrieval index.
3. OpenAI is not a part-number database.
4. The LLM must never invent part numbers.
5. Do not collapse the workbook into only one flat table.
6. Preserve duplicate part-number contexts.
7. Preserve source workbook, sheet, and row traceability.
8. Support future assembly-to-component and component-to-assembly lookup.
9. Support future domain synonyms and item aliases.
10. Store RFQ candidate evidence later for explainability, debugging, and user trust.

---

# Phase 1 Core Tables

These are the tables required for the first pricebook data foundation.

---

## 1. pricebook_versions

Stores each approved pricebook version.

| Column | SQL Type | Notes |
|---|---|---|
| pricebook_version_id | BIGINT IDENTITY PRIMARY KEY | Internal surrogate key |
| version_code | NVARCHAR(100) NOT NULL UNIQUE | Machine-friendly version code |
| version_name | NVARCHAR(255) NOT NULL | Human-readable version name |
| source_workbook_name | NVARCHAR(255) NOT NULL | Original workbook file name |
| source_file_hash | NVARCHAR(128) NULL | Optional file hash later |
| is_active | BIT NOT NULL DEFAULT 1 | Active approved version flag |
| created_at | DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME() | Audit timestamp |

Example:

```text
version_code = FT_PB_2022_JUN_FINAL_004
version_name = Fishing Tools PB 2022 Jun - Working File FINAL 004
```

---

## 2. pricebook_sections

Stores section-level information from the pricebook.

| Column | SQL Type | Notes |
|---|---|---|
| section_id | BIGINT IDENTITY PRIMARY KEY | Internal surrogate key |
| pricebook_version_id | BIGINT NOT NULL | FK to pricebook_versions |
| section_number | NVARCHAR(50) NOT NULL | Example: 1010 |
| sheet_number | NVARCHAR(50) NULL | Example: 1 |
| title | NVARCHAR(255) NULL | Example: Series 10 |
| source_sheet | NVARCHAR(255) NULL | Usually Data |
| created_at | DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME() | Audit timestamp |

Suggested uniqueness:

```text
pricebook_version_id + section_number + sheet_number + title
```

Reason:

The workbook can contain repeated titles or repeated sheet contexts. The combination gives better section identity than title alone.

---

## 3. parts

Stores unique part numbers.

| Column | SQL Type | Notes |
|---|---|---|
| part_id | BIGINT IDENTITY PRIMARY KEY | Internal surrogate key |
| part_number | NVARCHAR(100) NOT NULL | Original part number as text |
| part_number_normalized | NVARCHAR(100) NOT NULL | Normalized for exact lookup |
| is_placeholder | BIT NOT NULL DEFAULT 0 | True for N/A, TBD, blank-like values |
| created_at | DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME() | Audit timestamp |

Suggested uniqueness:

```text
part_number_normalized
```

Critical rule:

Part numbers must never be stored as INT, FLOAT, DECIMAL, or any numeric type.

Reason:

Part numbers may contain:

- letters
- slashes
- suffixes
- leading zeros
- special characters
- spaces in source data

---

## 4. pricebook_items

Stores contextual occurrences of a part in a pricebook version.

This is the main table for retrieval candidates.

| Column | SQL Type | Notes |
|---|---|---|
| pricebook_item_id | BIGINT IDENTITY PRIMARY KEY | Stable candidate/context ID |
| pricebook_version_id | BIGINT NOT NULL | FK to pricebook_versions |
| section_id | BIGINT NULL | FK to pricebook_sections |
| part_id | BIGINT NOT NULL | FK to parts |
| description | NVARCHAR(500) NULL | Item description |
| logan_part_number | NVARCHAR(100) NULL | Logan cross-reference if available |
| logan_description | NVARCHAR(500) NULL | Logan description if available |
| complete_assembly_number | NVARCHAR(100) NULL | Assembly context from workbook |
| is_valid_candidate | BIT NOT NULL DEFAULT 1 | False for placeholder/bad rows |
| invalid_reason | NVARCHAR(100) NULL | Example: placeholder_part_number |
| source_workbook | NVARCHAR(255) NOT NULL | Source workbook name |
| source_sheet | NVARCHAR(255) NOT NULL | Source sheet name |
| source_row_number | INT NOT NULL | Excel source row |
| created_at | DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME() | Audit timestamp |

Important:

Do not enforce uniqueness on `part_id` alone.

The same part may appear in multiple item contexts.

Example:

```text
part_id = 9791
description = Top Sub
complete_assembly_number = 9790
source_row_number = 3
```

---

## 5. attribute_definitions

Stores flexible attribute names.

| Column | SQL Type | Notes |
|---|---|---|
| attribute_definition_id | BIGINT IDENTITY PRIMARY KEY | Internal surrogate key |
| attribute_name | NVARCHAR(100) NOT NULL UNIQUE | Machine name, example: overshot_od |
| display_name | NVARCHAR(255) NOT NULL | Human name, example: Overshot OD |
| unit_hint | NVARCHAR(50) NULL | Example: inch |
| created_at | DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME() | Audit timestamp |

Reason:

Tool families have different technical attributes. A flexible attribute model is safer than creating too many fixed columns.

---

## 6. item_attributes

Stores flexible attributes for each pricebook item.

| Column | SQL Type | Notes |
|---|---|---|
| item_attribute_id | BIGINT IDENTITY PRIMARY KEY | Internal surrogate key |
| pricebook_item_id | BIGINT NOT NULL | FK to pricebook_items |
| attribute_definition_id | BIGINT NOT NULL | FK to attribute_definitions |
| attribute_value_text | NVARCHAR(255) NOT NULL | Original extracted value |
| attribute_value_normalized | NVARCHAR(255) NULL | Normalized value later |
| created_at | DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME() | Audit timestamp |

Suggested uniqueness:

```text
pricebook_item_id + attribute_definition_id + attribute_value_text
```

Example attributes:

- overshot_od
- size
- total_length
- catch_size
- nominal_size_or_catch_size
- shoe_od
- hole_size
- inside_diameter

---

## 7. item_search_index

Stores generated search text for each pricebook item.

| Column | SQL Type | Notes |
|---|---|---|
| item_search_index_id | BIGINT IDENTITY PRIMARY KEY | Internal surrogate key |
| pricebook_item_id | BIGINT NOT NULL UNIQUE | FK to pricebook_items |
| search_text | NVARCHAR(MAX) NOT NULL | Human-readable retrieval text |
| search_text_version | NVARCHAR(50) NOT NULL | Example: v1 |
| created_at | DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME() | Audit timestamp |

Example search text:

```text
Part Number: 9791 | Description: Top Sub | Title: Series 10 | Section: 1010 | Sheet: 1 | Complete Assembly Number: 9790 | Overshot OD: 1.5625
```

Important:

Qdrant vectors will later reference `pricebook_item_id`.

SQL remains the source of truth.

---

## 8. ingestion_runs

Stores ingestion execution metadata.

| Column | SQL Type | Notes |
|---|---|---|
| ingestion_run_id | BIGINT IDENTITY PRIMARY KEY | Internal surrogate key |
| pricebook_version_id | BIGINT NULL | FK to pricebook_versions |
| source_workbook_name | NVARCHAR(255) NOT NULL | Workbook name |
| input_row_count | INT NOT NULL | Input rows |
| output_row_count | INT NOT NULL | Output rows |
| valid_candidate_count | INT NOT NULL | Valid rows |
| invalid_candidate_count | INT NOT NULL | Invalid rows |
| duplicate_context_count | INT NOT NULL | Duplicate context rows |
| status | NVARCHAR(50) NOT NULL | started, success, failed |
| error_message | NVARCHAR(MAX) NULL | Failure reason |
| started_at | DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME() | Start time |
| finished_at | DATETIME2 NULL | End time |

---

# Strongly Recommended Early Tables

These tables are not strictly required for the first Excel-to-SQL load, but they are important for future relationship and terminology use cases.

---

## 9. part_relationships

Stores structured relationships between parts.

This supports questions like:

- Which assembly does this part belong to?
- What parts are associated with this assembly?
- What are the child components of this assembly?
- What assemblies use this part?

| Column | SQL Type | Notes |
|---|---|---|
| relationship_id | BIGINT IDENTITY PRIMARY KEY | Internal surrogate key |
| pricebook_version_id | BIGINT NOT NULL | FK to pricebook_versions |
| parent_part_id | BIGINT NOT NULL | Assembly or parent part |
| child_part_id | BIGINT NOT NULL | Component or child part |
| parent_pricebook_item_id | BIGINT NULL | Optional parent context |
| child_pricebook_item_id | BIGINT NULL | Optional child context |
| relationship_type | NVARCHAR(100) NOT NULL | Example: assembly_contains_component |
| relationship_source | NVARCHAR(100) NOT NULL | Example: complete_assembly_number |
| source_sheet | NVARCHAR(255) NULL | Source sheet |
| source_row_number | INT NULL | Source row |
| confidence_level | NVARCHAR(50) NOT NULL DEFAULT 'derived' | derived, verified, manual |
| is_verified | BIT NOT NULL DEFAULT 0 | SME-verified flag |
| created_at | DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME() | Audit timestamp |

Important:

Relationships derived from `Complete Assembly Number` should be marked as:

```text
confidence_level = derived
is_verified = 0
```

They should not be presented as engineering BOM truth unless verified.

---

## 10. domain_synonyms

Stores general domain terminology normalization rules.

Examples:

```text
CNTL -> control
F/- -> for
OD -> outside diameter
assy -> assembly
comp -> component
```

| Column | SQL Type | Notes |
|---|---|---|
| synonym_id | BIGINT IDENTITY PRIMARY KEY | Internal surrogate key |
| term | NVARCHAR(100) NOT NULL | User/raw term |
| canonical_term | NVARCHAR(100) NOT NULL | Normalized term |
| synonym_type | NVARCHAR(50) NULL | abbreviation, spelling, domain_term |
| applies_to_tool_family | NVARCHAR(255) NULL | Optional scope |
| is_active | BIT NOT NULL DEFAULT 1 | Active flag |
| created_at | DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME() | Audit timestamp |

Purpose:

This supports deterministic normalization before retrieval.

Qdrant alone is not enough for controlled terminology.

---

## 11. item_aliases

Stores aliases tied to a specific part or item.

| Column | SQL Type | Notes |
|---|---|---|
| item_alias_id | BIGINT IDENTITY PRIMARY KEY | Internal surrogate key |
| part_id | BIGINT NULL | FK to parts |
| pricebook_item_id | BIGINT NULL | FK to pricebook_items |
| alias_text | NVARCHAR(255) NOT NULL | Alternate name |
| alias_type | NVARCHAR(50) NULL | customer_term, legacy_name, logan_cross_reference |
| source | NVARCHAR(100) NULL | SME, workbook, user_feedback |
| is_active | BIT NOT NULL DEFAULT 1 | Active flag |
| created_at | DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME() | Audit timestamp |

Difference:

```text
domain_synonyms = general language normalization
item_aliases = alternate names linked to a specific part or item
```

---

# Future Phase 2+ Tables

These tables are not part of the first pricebook load.

---

## rfq_requests

Stores RFQ search sessions.

Future use only.

---

## rfq_lines

Stores parsed RFQ lines.

Future use only.

---

## rfq_match_candidates

Stores candidates returned for each RFQ line.

Future use only.

---

## rfq_candidate_evidence

Stores evidence behind each candidate recommendation.

This improves:

- explainability
- debugging
- evaluation
- user trust
- ranking analysis

Example evidence:

- exact part-number match
- assembly-number match
- keyword match
- synonym match
- attribute match
- semantic match
- source row match

Suggested columns:

| Column | SQL Type | Notes |
|---|---|---|
| evidence_id | BIGINT IDENTITY PRIMARY KEY | Internal surrogate key |
| rfq_match_candidate_id | BIGINT NOT NULL | FK added later |
| retrieval_method | NVARCHAR(100) NOT NULL | exact, keyword, synonym, semantic, attribute |
| matched_field | NVARCHAR(100) NULL | description, assembly_number, part_number |
| matched_value | NVARCHAR(500) NULL | Value that matched |
| query_term | NVARCHAR(500) NULL | RFQ/query term |
| score | DECIMAL(10,4) NULL | Retrieval score |
| rank_contribution | DECIMAL(10,4) NULL | Contribution to final rank |
| source_table | NVARCHAR(100) NULL | Source table |
| source_record_id | BIGINT NULL | Source record |
| explanation | NVARCHAR(MAX) NULL | Human-readable explanation |
| created_at | DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME() | Audit timestamp |

Reason this is future phase:

RFQ candidate evidence depends on runtime RFQ matching tables.

---

## rfq_match_feedback

Stores user feedback on match quality.

Future use only.

---

# Relationship Query Examples

## What parts belong to assembly 9790?

SQL approach:

```text
parts.part_number_normalized = 9790
-> part_relationships.parent_part_id
-> child_part_id
-> parts.part_number
```

## Which assembly does part 9791 belong to?

SQL approach:

```text
parts.part_number_normalized = 9791
-> part_relationships.child_part_id
-> parent_part_id
-> parts.part_number
```

## What if the user uses vague wording?

Use:

```text
domain_synonyms
+ SQL keyword search
+ Qdrant semantic search
+ SQL relationship lookup
```

The relationship answer still comes from SQL.

---

# Long-Term Knowledge Architecture

The intended long-term architecture is:

```text
SQL Server
-> source of truth for parts, item contexts, assemblies, relationships, aliases, evidence, and feedback

Qdrant
-> semantic retrieval for vague wording and similarity search

domain_synonyms / item_aliases
-> deterministic terminology normalization

OpenAI / LLM
-> extraction, reasoning, explanation, and validation over retrieved facts only

MLflow
-> evaluation, prompt/model/search-version tracking, metrics, and experiment history
```

## LLM Rule

The LLM may explain relationships, but it must not invent them.

If SQL does not contain the relationship, the system should say:

```text
No approved relationship found in the current pricebook data.
```

---

# First Migration Recommendation

For the first SQL DDL migration, implement:

- pricebook_versions
- pricebook_sections
- parts
- pricebook_items
- attribute_definitions
- item_attributes
- item_search_index
- ingestion_runs

Strongly consider implementing early:

- part_relationships
- domain_synonyms
- item_aliases

Do not implement yet:

- rfq_requests
- rfq_lines
- rfq_match_candidates
- rfq_candidate_evidence
- rfq_match_feedback
- llm_runs
- ai_run_references
- item_embeddings

Those belong to later phases.

---

# Recommended Initial Indexes

Initial indexes:

```sql
CREATE INDEX IX_parts_part_number_normalized
ON parts(part_number_normalized);

CREATE INDEX IX_pricebook_items_valid_candidate
ON pricebook_items(is_valid_candidate);

CREATE INDEX IX_pricebook_items_assembly
ON pricebook_items(complete_assembly_number);

CREATE INDEX IX_pricebook_items_source
ON pricebook_items(source_workbook, source_sheet, source_row_number);

CREATE INDEX IX_item_attributes_name_value
ON item_attributes(attribute_definition_id, attribute_value_normalized);
```

Later search indexes may be added after the SQL retrieval baseline is tested.

---

# Next Engineering Step

After this document is committed, create the first SQL DDL file:

```text
alembic/manual_sql/001_create_pricebook_tables.sql
```

Do not connect to SQL Server until the DDL file is reviewed.
