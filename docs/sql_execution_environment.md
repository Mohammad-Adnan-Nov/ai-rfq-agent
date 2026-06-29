# SQL Execution Environment Decision

## Purpose

This document records the first SQL Server environment selected for testing the Phase 1 SQL DDL.

The DDL file is:

```text
alembic/manual_sql/001_create_pricebook_tables.sql
```

## Current Decision

Do not run the DDL in production.

The first execution should happen in a local or development SQL Server environment.

## Preferred Execution Order

1. Local SQL Server Express or SQL Server Developer Edition
2. NOV development SQL Server database
3. Test or staging SQL Server database
4. Production only after review and approval

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

## Local Environment Check Results

### LocalDB Check

Command:

```powershell
sqllocaldb info
```

Result:

```text
sqllocaldb is not recognized.
```

Interpretation:

LocalDB is not installed or not available in PATH.

This is not a blocker because SQL Server Express is available.

### SQL Server Service Check

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

## Selected First Execution Target

The selected first execution target is:

```text
.\SQLEXPRESS
```

This is a local SQL Server Express instance.

## Why SQL Server Express Is Acceptable

SQL Server Express is suitable for first DDL validation because:

- it is local
- it avoids production risk
- SQL Server syntax and constraints can be tested
- table creation can be verified safely
- the database can be deleted and recreated if needed

## Remaining Preflight Check

Before running the DDL, confirm whether `sqlcmd` is installed.

Use:

```powershell
Get-Command sqlcmd -ErrorAction SilentlyContinue
```

or:

```powershell
where.exe sqlcmd
```

If `sqlcmd` is available, we can run the DDL from PowerShell.

If `sqlcmd` is not available, we can use SQL Server Management Studio, Azure Data Studio, or install the SQL Server command-line tools.

## Current Execution Decision

```text
Do not run the SQL DDL yet.
```

## Next Step

Run a connection preflight against:

```text
.\SQLEXPRESS
```

Then create a local development database for this project.
