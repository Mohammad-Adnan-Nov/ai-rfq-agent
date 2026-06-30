# SQL Execution Environment Decision

## Purpose

This document records the SQL Server environment selected for testing the Phase 1 SQL DDL for the AI RFQ Agent.

The DDL file is:

```text
alembic/manual_sql/001_create_pricebook_tables.sql
```

This document exists so that the project has a clear record of:

- which SQL Server environment was selected
- why production was not used first
- how the local SQL Server connection was verified
- which local database was created for testing
- what must happen before running the DDL anywhere else

---

## Current Execution Decision

```text
Do not run the SQL DDL in production.
Run the DDL locally first in AI_RFQ_AGENT_DEV on .\SQLEXPRESS.
```

---

## Preferred Execution Order

The safe execution order is:

1. Local SQL Server Express or SQL Server Developer Edition
2. NOV development SQL Server database
3. Test or staging SQL Server database
4. Production only after review, approval, backup, and rollback planning

---

## Why Not Production First

The DDL creates:

- schema
- tables
- primary keys
- foreign keys
- check constraints
- unique indexes
- seed data

Running it directly in production before local validation creates unnecessary risk.

Local execution allows us to validate the SQL Server syntax, schema, constraints, indexes, and seed data safely.

---

## LocalDB Check

Command:

```powershell
sqllocaldb info
```

Observed result:

```text
sqllocaldb : The term 'sqllocaldb' is not recognized as the name of a cmdlet, function, script file, or operable program.
```

Interpretation:

LocalDB is not installed or is not available in PATH.

This is not a blocker because SQL Server Express is installed and running locally.

---

## SQL Server Service Check

Command:

```powershell
Get-Service | Where-Object { $_.Name -like "MSSQL*" -or $_.Name -like "SQL*" } | Select-Object Name, Status, DisplayName
```

Observed result:

```text
Name                     Status  DisplayName
----                     ------  -----------
MSSQL$SQLEXPRESS         Running SQL Server (SQLEXPRESS)
SQLAgent$SQLEXPRESS      Stopped SQL Server Agent (SQLEXPRESS)
SQLBrowser               Stopped SQL Server Browser
SQLTELEMETRY$SQLEXPRESS  Running SQL Server CEIP service (SQLEXPRESS)
SQLWriter                Running SQL Server VSS Writer
```

Interpretation:

SQL Server Express is installed and running locally.

The selected first SQL Server target is:

```text
.\SQLEXPRESS
```

---

## sqlcmd Availability Check

Commands:

```powershell
Get-Command sqlcmd -ErrorAction SilentlyContinue
where.exe sqlcmd
```

Observed result:

```text
CommandType     Name        Version     Source
-----------     ----        -------     ------
Application     SQLCMD.EXE  15.0.20...  C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE

C:\Program Files\Microsoft SQL Server\Client SDK\ODBC\170\Tools\Binn\SQLCMD.EXE
```

Interpretation:

`sqlcmd` is installed and available from PowerShell.

This means SQL Server commands and SQL files can be executed from the terminal.

---

## SQL Server Connection Preflight

Command:

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -Q "SELECT @@SERVERNAME AS server_name, @@SERVICENAME AS service_name;"
```

Observed result:

```text
server_name              service_name
----------------------   ------------
5CD5196NXP\SQLEXPRESS    SQLEXPRESS
```

Interpretation:

PowerShell can connect to the local SQL Server Express instance.

Windows authentication works.

The SQL Server instance name is valid:

```text
.\SQLEXPRESS
```

---

## Existing Database Check Before Project Database Creation

Command:

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -Q "SELECT name FROM sys.databases ORDER BY name;"
```

Observed result:

```text
name
----
master
model
msdb
tempdb
```

Interpretation:

Only the default system databases were present before creating the local AI RFQ Agent development database.

No project database existed yet.

---

## Selected Local Development Database

Selected local development database:

```text
AI_RFQ_AGENT_DEV
```

Reason:

This database is dedicated to local testing for the AI RFQ Agent.

The Phase 1 DDL should be tested here before it is run in any NOV development, staging, or production SQL Server environment.

---

## Local Development Database Creation

Command:

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -Q "IF DB_ID(N'AI_RFQ_AGENT_DEV') IS NULL CREATE DATABASE [AI_RFQ_AGENT_DEV];"
```

Purpose:

This creates the local development database only if it does not already exist.

This makes the command safe to run more than once.

---

## Local Development Database Verification

Command:

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -Q "SELECT name FROM sys.databases WHERE name = N'AI_RFQ_AGENT_DEV';"
```

Expected result:

```text
name
----------------
AI_RFQ_AGENT_DEV
```

Purpose:

This confirms that the local project database exists.

---

## Empty Database Verification

Command:

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES ORDER BY TABLE_SCHEMA, TABLE_NAME;"
```

Expected result before DDL execution:

```text
No user tables should exist.
```

Purpose:

This confirms that the database is clean before running the Phase 1 DDL.

---

## Selected First Execution Target

The selected first execution target is:

```text
Server: .\SQLEXPRESS
Database: AI_RFQ_AGENT_DEV
Schema to be created by DDL: rfq
```

---

## Why SQL Server Express Is Acceptable for First Execution

SQL Server Express is acceptable for the first DDL validation because:

- it is local
- it avoids production risk
- it supports SQL Server table, constraint, index, and schema validation
- the database can be deleted and recreated if needed
- no NOV shared or production environment is touched

---

## DDL Execution Status

Current status:

```text
DDL has not been executed yet.
```

Next intended command:

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -b -i "alembic\manual_sql\001_create_pricebook_tables.sql" -o "data\processed\sql_ddl_execution_output.txt"
```

Purpose:

This will execute the Phase 1 DDL locally only.

The output will be written to:

```text
data\processed\sql_ddl_execution_output.txt
```

Important:

This output file is generated local output and should not be committed.

---

## Post-DDL Validation Commands

After executing the DDL locally, run:

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "SELECT name FROM sys.schemas WHERE name = 'rfq';"
```

Purpose:

Confirms the `rfq` schema exists.

Then run:

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_SCHEMA = 'rfq' ORDER BY TABLE_NAME;"
```

Purpose:

Confirms the expected Phase 1 tables were created.

Then run:

```powershell
sqlcmd -S ".\SQLEXPRESS" -E -d "AI_RFQ_AGENT_DEV" -Q "SELECT COUNT(*) AS attribute_count FROM rfq.attribute_definitions; SELECT COUNT(*) AS relationship_type_count FROM rfq.relationship_type_definitions;"
```

Expected result:

```text
attribute_count = 11
relationship_type_count = 3
```

Purpose:

Confirms that required seed data was inserted.

---

## Safety Rules

Do not run the DDL against:

- production
- a shared NOV database
- any database you do not own
- any database that has not been approved for testing

Only run the DDL first against:

```text
.\SQLEXPRESS
AI_RFQ_AGENT_DEV
```

---

## Current Project Status

Current status:

```text
Ready for local DDL execution.
```

Next step:

```text
Phase 1 - Step 17: Execute Phase 1 DDL locally in AI_RFQ_AGENT_DEV.
```
