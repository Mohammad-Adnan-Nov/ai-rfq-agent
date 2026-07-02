# SQL Command Reference

This document records the SQL Server and `sqlcmd` commands used during Phase 1 of the AI RFQ Agent project.

## Scope

These commands are for the local development SQL Server environment only.

```text
Server: .\SQLEXPRESS
Database: AI_RFQ_AGENT_DEV
Schema: rfq
```

Do not run these commands against a production or shared NOV SQL Server unless the environment, database name, permissions, and data governance rules have been reviewed.

## Important project rules

- SQL Server is the source of truth for structured pricebook and part data.
- Qdrant, later, is only a semantic/vector retrieval index.
- The LLM must not invent part numbers.
- Part numbers must be stored as text, not numeric types.
- Duplicate part-number contexts must be preserved.
- Generated files under `data/processed` should not be committed.
- Raw Excel workbooks under `data/raw` should not be committed.

---

# 1. SQL Server environment checks

## 1.1 Check whether LocalDB exists

### Purpose

Check whether SQL Server LocalDB is installed.

### Command

```powershell
sqllocaldb info
```

### Expected result

In this project, LocalDB was not available. That is not a blocker because SQL Server Express is available.

---

## 1.2 Check SQL Server services

### Purpose

Confirm that SQL Server Express is installed and running.

### Command

```powershell
Get-Service | Where-Object {
    $_.Name -like "*SQL*" -or $_.DisplayName -like "*SQL*"
} | Sort-Object Name
```

### Expected result

Expected service:

```text
MSSQL$SQLEXPRESS        Running
```

SQL Server Agent may be stopped. That is acceptable for this local development workflow.

---

## 1.3 Check whether `sqlcmd` is installed

### Purpose

Confirm that the command-line SQL Server client is available.

### Command

```powershell
Get-Command sqlcmd -ErrorAction SilentlyContinue
where.exe sqlcmd
```

### Expected result

Example:

```text
C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE
```

---

## 1.4 Test SQL Server connection

### Purpose

Verify that Windows authentication can connect to the local SQL Server Express instance.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -Q "SELECT @@SERVERNAME AS server_name, @@SERVICENAME AS service_name;"
```

### Expected result

Example:

```text
server_name             service_name
----------------------  ------------
5CD5196NXP\SQLEXPRESS   SQLEXPRESS
```

---

# 2. Local development database commands

## 2.1 List existing databases

### Purpose

Check which databases exist before creating the project database.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -Q "SELECT name FROM sys.databases ORDER BY name;"
```

### Expected result before project database creation

Expected built-in databases:

```text
master
model
msdb
tempdb
```

---

## 2.2 Create local development database

### Purpose

Create the local project database if it does not already exist.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -Q "IF DB_ID(N'AI_RFQ_AGENT_DEV') IS NULL CREATE DATABASE [AI_RFQ_AGENT_DEV];"
```

### Expected result

No error.

---

## 2.3 Verify local development database exists

### Purpose

Confirm that `AI_RFQ_AGENT_DEV` exists.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -Q "SELECT name FROM sys.databases WHERE name = N'AI_RFQ_AGENT_DEV';"
```

### Expected result

```text
name
--------------------
AI_RFQ_AGENT_DEV
```

---

# 3. Pre-DDL checks

## 3.1 Check whether target database is empty before DDL

### Purpose

Verify that the database has no existing user tables before running the DDL.

This matters because the current DDL is not fully idempotent. Running it into a database that already contains the same objects may fail.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_SCHEMA, TABLE_NAME;"
```

### Expected result before first DDL execution

No user tables should be returned.

---

# 4. DDL execution

## 4.1 Execute Phase 1 DDL locally

### Purpose

Create the `rfq` schema, Phase 1 tables, constraints, indexes, and seed data.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -b -i "alembic\manual_sql\001_create_pricebook_tables.sql" -o "data\processed\sql_ddl_execution_output.txt"
```

### Expected result

The command should return to the PowerShell prompt without error.

The `-b` flag makes `sqlcmd` return an error exit code when SQL Server reports an execution error.

### Output file

```text
data\processed\sql_ddl_execution_output.txt
```

Do not commit this generated output file.

---

## 4.2 Inspect DDL execution output

### Purpose

Check for hidden SQL execution errors or warnings.

### Command

```powershell
Get-Content data\processed\sql_ddl_execution_output.txt -TotalCount 120
```

### Error search command

```powershell
Select-String -Path data\processed\sql_ddl_execution_output.txt -Pattern "Msg","Error","Incorrect syntax","already an object","Foreign key","failed"
```

### Expected result

The error search should return no relevant SQL errors.

---

# 5. Post-DDL schema validation

## 5.1 Verify `rfq` schema exists

### Purpose

Confirm that the DDL created the project schema.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "SELECT name FROM sys.schemas WHERE name = 'rfq';"
```

### Expected result

```text
name
----
rfq
```

---

## 5.2 Verify expected `rfq` tables exist

### Purpose

Confirm that the expected Phase 1 tables were created.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'rfq' ORDER BY TABLE_NAME;"
```

### Expected tables

```text
attribute_definitions
domain_synonyms
ingestion_runs
item_aliases
item_attributes
item_search_index
part_relationships
parts
pricebook_items
pricebook_sections
pricebook_versions
relationship_type_definitions
```

---

## 5.3 Verify seed counts

### Purpose

Confirm that required seed rows were inserted.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "SELECT COUNT(*) AS attribute_count FROM rfq.attribute_definitions; SELECT COUNT(*) AS relationship_type_count FROM rfq.relationship_type_definitions;"
```

### Expected result

```text
attribute_count = 11
relationship_type_count = 3
```

### Expected seeded attributes

```text
overshot_od
size
total_length
diameter_largest_wicker
diameter_smallest_wicker
catch_size
nominal_size_or_catch_size
assembly_dressed_to_packoff
shoe_od
hole_size
inside_diameter
```

### Expected seeded relationship types

```text
assembly_contains_component
cross_reference
alternate_part
```

---

## 5.4 Verify constraints

### Purpose

Confirm that primary keys, foreign keys, unique constraints, and check constraints exist.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "SELECT name, type_desc FROM sys.objects WHERE schema_id = SCHEMA_ID('rfq') AND (name LIKE 'PK_%' OR name LIKE 'FK_%' OR name LIKE 'UQ_%' OR name LIKE 'CK_%') ORDER BY name;"
```

### Expected important constraints

Examples:

```text
UQ_pricebook_items_source_row
CK_ingestion_runs_status
CK_part_relationships_confidence_level
CK_part_relationships_no_self_reference
CK_part_relationships_no_same_pricebook_item
```

---

## 5.5 Verify indexes

### Purpose

Confirm that indexes were created for retrieval, uniqueness, and validation support.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "SELECT i.name AS index_name, OBJECT_NAME(i.object_id) AS table_name FROM sys.indexes i WHERE OBJECT_SCHEMA_NAME(i.object_id) = 'rfq' AND i.name IS NOT NULL ORDER BY table_name, index_name;"
```

### Expected result

Indexes should exist across important tables such as:

```text
parts
pricebook_items
pricebook_versions
pricebook_sections
item_attributes
item_search_index
part_relationships
domain_synonyms
item_aliases
```

---

# 6. SQL schema inspection exports

## 6.1 Export SQL columns after DDL

### Purpose

Create a local inspection file showing table columns, data types, max lengths, and nullability.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -W -s "," -Q "
SET NOCOUNT ON;

SELECT
    TABLE_SCHEMA,
    TABLE_NAME,
    ORDINAL_POSITION,
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'rfq'
ORDER BY TABLE_NAME, ORDINAL_POSITION;
" -o "data\processed\sql_schema_columns_after_ddl.csv"
```

### Output file

```text
data\processed\sql_schema_columns_after_ddl.csv
```

Do not commit this generated output file.

### Note

`sqlcmd -s ","` may include a dashed separator row after the header. Treat this as a human inspection file, not a clean machine-readable CSV.

---

## 6.2 Export SQL identity columns

### Purpose

Identify auto-generated identity columns so the loader does not try to manually insert IDs.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -W -s "," -Q "
SET NOCOUNT ON;

SELECT
    OBJECT_SCHEMA_NAME(c.object_id) AS schema_name,
    OBJECT_NAME(c.object_id) AS table_name,
    c.name AS column_name,
    c.is_identity
FROM sys.columns c
WHERE OBJECT_SCHEMA_NAME(c.object_id) = 'rfq'
  AND c.is_identity = 1
ORDER BY table_name, column_name;
" -o "data\processed\sql_identity_columns_after_ddl.csv"
```

### Output file

```text
data\processed\sql_identity_columns_after_ddl.csv
```

Do not commit this generated output file.

---

# 7. Pre-load SQL checks

## 7.1 Verify target load tables are empty

### Purpose

Confirm that no previous load data exists before running the SQL loader.

The current loader is designed for the first clean load and refuses to load into non-empty target tables.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "
SELECT 'pricebook_versions' AS table_name, COUNT(*) AS row_count FROM rfq.pricebook_versions
UNION ALL SELECT 'pricebook_sections', COUNT(*) FROM rfq.pricebook_sections
UNION ALL SELECT 'parts', COUNT(*) FROM rfq.parts
UNION ALL SELECT 'pricebook_items', COUNT(*) FROM rfq.pricebook_items
UNION ALL SELECT 'item_attributes', COUNT(*) FROM rfq.item_attributes
UNION ALL SELECT 'item_search_index', COUNT(*) FROM rfq.item_search_index
UNION ALL SELECT 'ingestion_runs', COUNT(*) FROM rfq.ingestion_runs
ORDER BY table_name;
"
```

### Expected result before first load

```text
ingestion_runs        0
item_attributes       0
item_search_index     0
parts                 0
pricebook_items       0
pricebook_sections    0
pricebook_versions    0
```

---

# 8. Loader-related commands

These are not raw SQL commands, but they are part of the SQL loading workflow.

## 8.1 Run SQL loader dry-run

### Purpose

Validate CSV-to-SQL preparation without inserting rows into SQL Server.

### Command

```powershell
python scripts\load_pricebook_to_sql.py `
  --server ".\SQLEXPRESS" `
  --database "AI_RFQ_AGENT_DEV" `
  --input-csv "data\processed\pricebook_items_preview.csv" `
  --source-workbook "data\raw\Fishing Tools PB 2022 (Jun) - Working File FINAL 004.xlsx" `
  --dry-run
```

### Expected result

Expected key values:

```text
csv_row_count = 12092
pricebook_item_count = 12092
valid_candidate_count = 11138
invalid_candidate_count = 954
search_index_row_count_prepared = 11138
status = dry_run_completed
```

---

## 8.2 Run actual SQL load

### Purpose

Load canonical pricebook item records into SQL Server.

### Command

```powershell
python scripts\load_pricebook_to_sql.py `
  --server ".\SQLEXPRESS" `
  --database "AI_RFQ_AGENT_DEV" `
  --input-csv "data\processed\pricebook_items_preview.csv" `
  --source-workbook "data\raw\Fishing Tools PB 2022 (Jun) - Working File FINAL 004.xlsx"
```

### Expected result

```text
SQL load completed successfully.
```

### Output file

```text
data\processed\sql_pricebook_load_report.json
```

Do not commit this generated output file.

---

# 9. Troubleshooting SQL constraint errors

## 9.1 Inspect `CK_ingestion_runs_status`

### Purpose

Check allowed values for the `rfq.ingestion_runs.status` column.

This was needed after SQL Server rejected an unsupported status value during loader execution.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "
SELECT
    cc.name AS constraint_name,
    cc.definition
FROM sys.check_constraints cc
JOIN sys.tables t
    ON t.object_id = cc.parent_object_id
JOIN sys.schemas s
    ON s.schema_id = t.schema_id
WHERE s.name = 'rfq'
  AND t.name = 'ingestion_runs'
  AND cc.name = 'CK_ingestion_runs_status';
"
```

### Expected result

The result should show the allowed values for the `status` column.

The Python loader must use one of the allowed database values.

---

## 9.2 Verify rollback after failed load

### Purpose

Confirm that a failed SQL load did not leave partial rows in target tables.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "
SELECT 'pricebook_versions' AS table_name, COUNT(*) AS row_count FROM rfq.pricebook_versions
UNION ALL SELECT 'pricebook_sections', COUNT(*) FROM rfq.pricebook_sections
UNION ALL SELECT 'parts', COUNT(*) FROM rfq.parts
UNION ALL SELECT 'pricebook_items', COUNT(*) FROM rfq.pricebook_items
UNION ALL SELECT 'item_attributes', COUNT(*) FROM rfq.item_attributes
UNION ALL SELECT 'item_search_index', COUNT(*) FROM rfq.item_search_index
UNION ALL SELECT 'ingestion_runs', COUNT(*) FROM rfq.ingestion_runs
ORDER BY table_name;
"
```

### Expected result after rollback

All target load tables should still be zero if rollback succeeded.

---

# 10. Post-load validation commands

## 10.1 Verify final SQL table counts

### Purpose

Confirm that SQL Server contains the expected loaded rows.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "
SELECT 'pricebook_versions' AS table_name, COUNT(*) AS row_count FROM rfq.pricebook_versions
UNION ALL SELECT 'pricebook_sections', COUNT(*) FROM rfq.pricebook_sections
UNION ALL SELECT 'parts', COUNT(*) FROM rfq.parts
UNION ALL SELECT 'pricebook_items', COUNT(*) FROM rfq.pricebook_items
UNION ALL SELECT 'item_attributes', COUNT(*) FROM rfq.item_attributes
UNION ALL SELECT 'item_search_index', COUNT(*) FROM rfq.item_search_index
UNION ALL SELECT 'ingestion_runs', COUNT(*) FROM rfq.ingestion_runs
ORDER BY table_name;
"
```

### Expected result after successful load

Required:

```text
pricebook_versions    1
pricebook_items       12092
item_search_index     11138
ingestion_runs        1
```

Also expected:

```text
pricebook_sections    greater than 0
parts                 greater than 0
item_attributes       greater than 0
```

---

## 10.2 Verify valid and invalid candidate counts

### Purpose

Confirm that SQL candidate counts match the canonical item-record CSV.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "
SELECT
    is_valid_candidate,
    COUNT(*) AS row_count
FROM rfq.pricebook_items
GROUP BY is_valid_candidate
ORDER BY is_valid_candidate DESC;
"
```

### Expected result

```text
is_valid_candidate  row_count
------------------  ---------
1                   11138
0                   954
```

---

## 10.3 Verify ingestion run summary

### Purpose

Confirm that the ingestion run metadata was saved correctly.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "
SELECT
    ingestion_run_id,
    input_row_count,
    output_row_count,
    valid_candidate_count,
    invalid_candidate_count,
    duplicate_context_count,
    status,
    started_at,
    finished_at
FROM rfq.ingestion_runs;
"
```

### Expected result

Expected values:

```text
input_row_count           12092
output_row_count          12092
valid_candidate_count     11138
invalid_candidate_count   954
status                    completed/succeeded/success, depending on DDL constraint
```

Use the actual status allowed by `CK_ingestion_runs_status`.

---

## 10.4 Verify source traceability

### Purpose

Confirm that loaded pricebook item rows retain workbook, sheet, and source row traceability.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "
SELECT TOP 20
    pi.pricebook_item_id,
    p.part_number,
    pi.description,
    pi.source_workbook,
    pi.source_sheet,
    pi.source_row_number
FROM rfq.pricebook_items pi
JOIN rfq.parts p
    ON p.part_id = pi.part_id
ORDER BY pi.pricebook_item_id;
"
```

### Expected result

Each row should show:

```text
source_workbook = Fishing Tools PB 2022 (Jun) - Working File FINAL 004.xlsx
source_sheet    = Data
source_row_number populated
```

---

## 10.5 Verify search text examples

### Purpose

Confirm that valid candidates have readable search text for future retrieval.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "
SELECT TOP 10
    p.part_number,
    pi.description,
    LEFT(si.search_text, 300) AS search_text_preview
FROM rfq.item_search_index si
JOIN rfq.pricebook_items pi
    ON pi.pricebook_item_id = si.pricebook_item_id
JOIN rfq.parts p
    ON p.part_id = pi.part_id
ORDER BY si.item_search_index_id;
"
```

### Expected result

`search_text_preview` should contain readable text with part number, description, title/section context, and technical attributes where available.

---

## 10.6 Verify invalid rows are excluded from search index

### Purpose

Invalid rows should remain in `pricebook_items` for traceability, but should not appear in `item_search_index` as retrievable candidates.

### Command

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "
SELECT COUNT(*) AS invalid_rows_in_search_index
FROM rfq.item_search_index si
JOIN rfq.pricebook_items pi
    ON pi.pricebook_item_id = si.pricebook_item_id
WHERE pi.is_valid_candidate = 0;
"
```

### Expected result

```text
invalid_rows_in_search_index
----------------------------
0
```

---

# 11. Files not to commit

Do not commit generated files such as:

```text
data\processed\sql_ddl_execution_output.txt
data\processed\sql_schema_columns_after_ddl.csv
data\processed\sql_identity_columns_after_ddl.csv
data\processed\sql_pricebook_load_report.json
data\processed\pricebook_items_preview.csv
data\processed\pricebook_items_quality_report.json
data\processed\item_quality_report.json
data\processed\workbook_profile.json
data\processed\data_sheet_preview.json
```

Do not commit raw workbook files such as:

```text
data\raw\Fishing Tools PB 2022 (Jun) - Working File FINAL 004.xlsx
```
