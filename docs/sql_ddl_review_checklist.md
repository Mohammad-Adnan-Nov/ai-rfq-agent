# SQL DDL Review Checklist

## Purpose

This checklist is used before running the Phase 1 SQL DDL against any SQL Server database.

Current DDL file:

```text
alembic/manual_sql/001_create_pricebook_tables.sql
```

Current DDL status:

```text
Production-oriented V1 draft
```

Current execution decision:

```text
Do not run the SQL DDL in production.
Run locally or in a development SQL Server database first.
```

---

## 1. Architecture Governance

| Check | Status |
|---|---|
| SQL Server is treated as the source of truth | Pending |
| Qdrant is not treated as source of truth | Pending |
| OpenAI/LLM is not treated as source of truth | Pending |
| RFQ runtime tables are not included in Phase 1 DDL | Pending |
| Part numbers are stored as text, not numeric types | Pending |
| Source traceability is preserved | Pending |
| Duplicate part-number contexts are allowed | Pending |
| Delete behavior is restricted by default, not cascaded | Pending |

---

## 2. Schema Review

Expected schema:

```text
rfq
```

| Check | Status |
|---|---|
| DDL creates rfq schema if missing | Pending |
| Tables are created under rfq schema, not dbo | Pending |
| Schema naming is appropriate for future shared database use | Pending |

---

## 3. Expected Table Creation Order

Expected table dependency order:

1. rfq.pricebook_versions
2. rfq.pricebook_sections
3. rfq.parts
4. rfq.pricebook_items
5. rfq.attribute_definitions
6. rfq.item_attributes
7. rfq.item_search_index
8. rfq.ingestion_runs
9. rfq.relationship_type_definitions
10. rfq.part_relationships
11. rfq.domain_synonyms
12. rfq.item_aliases

| Check | Status |
|---|---|
| Parent tables are created before child tables | Pending |
| Foreign keys reference existing tables | Pending |
| No circular required dependencies exist | Pending |
| RFQ transaction tables are excluded | Pending |

---

## 4. pricebook_versions Review

Expected purpose:

Stores approved pricebook versions.

| Check | Status |
|---|---|
| Has primary key | Pending |
| product_family exists | Pending |
| version_code is unique | Pending |
| version_name exists | Pending |
| source_workbook_name exists | Pending |
| source_file_hash exists | Pending |
| is_active exists | Pending |
| created_at exists | Pending |
| Only one active version per product_family is enforced | Pending |

Important:

`source_file_hash` may remain nullable in the database during early development, but production ingestion should calculate and store it.

---

## 5. pricebook_sections Review

Expected purpose:

Stores section and sheet context.

| Check | Status |
|---|---|
| Has primary key | Pending |
| Has FK to pricebook_versions | Pending |
| section_number is text | Pending |
| section_number_normalized exists | Pending |
| sheet_number is text | Pending |
| sheet_number_normalized exists | Pending |
| title exists | Pending |
| title_normalized exists | Pending |
| source_sheet exists | Pending |
| Uniqueness uses normalized section context | Pending |

Expected uniqueness logic:

```text
pricebook_version_id
section_number_normalized
sheet_number_normalized
title_normalized
source_sheet
```

---

## 6. parts Review

Expected purpose:

Stores unique part numbers.

| Check | Status |
|---|---|
| Has primary key | Pending |
| part_number is NVARCHAR | Pending |
| part_number_normalized is NVARCHAR | Pending |
| part_number_normalized is unique | Pending |
| is_placeholder exists | Pending |
| created_at exists | Pending |
| No numeric type is used for part numbers | Pending |

Critical rule:

Part numbers must never be stored as INT, FLOAT, DECIMAL, or any numeric type.

---

## 7. pricebook_items Review

Expected purpose:

Stores each source-row item context from the pricebook.

| Check | Status |
|---|---|
| Has primary key | Pending |
| Has FK to pricebook_versions | Pending |
| Has FK to pricebook_sections | Pending |
| Has FK to parts | Pending |
| description is large enough | Pending |
| logan_part_number is text | Pending |
| logan_description is text | Pending |
| complete_assembly_number is text | Pending |
| is_valid_candidate exists | Pending |
| invalid_reason exists | Pending |
| source_workbook exists | Pending |
| source_sheet exists | Pending |
| source_row_number exists | Pending |
| Same source row cannot be loaded twice for same version | Pending |
| Does not enforce uniqueness on part_id alone | Pending |

Important:

The same part number may appear in multiple pricebook contexts. This is expected and must not be blocked.

---

## 8. attribute_definitions Review

Expected purpose:

Stores flexible technical attribute names.

| Check | Status |
|---|---|
| Has primary key | Pending |
| attribute_name is unique | Pending |
| display_name exists | Pending |
| unit_hint exists | Pending |
| Seed values are included for current technical attributes | Pending |

Expected seeded attributes:

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

---

## 9. item_attributes Review

Expected purpose:

Stores flexible attribute values for each pricebook item.

| Check | Status |
|---|---|
| Has primary key | Pending |
| Has FK to pricebook_items | Pending |
| Has FK to attribute_definitions | Pending |
| attribute_value_text stores original extracted value | Pending |
| attribute_value_normalized exists for future normalization | Pending |
| Attribute values are stored as text | Pending |
| One value per pricebook_item_id and attribute_definition_id is enforced | Pending |

Expected uniqueness:

```text
pricebook_item_id + attribute_definition_id
```

---

## 10. item_search_index Review

Expected purpose:

Stores generated search text for each pricebook item.

| Check | Status |
|---|---|
| Has primary key | Pending |
| Has FK to pricebook_items | Pending |
| One search index row per pricebook_item_id is enforced | Pending |
| search_text is NVARCHAR(MAX) | Pending |
| search_text_version exists | Pending |
| created_at exists | Pending |

Important:

Qdrant vectors should later reference `pricebook_item_id`.

SQL remains the source of truth.

---

## 11. ingestion_runs Review

Expected purpose:

Stores ingestion metadata and audit information.

| Check | Status |
|---|---|
| Has primary key | Pending |
| Has optional FK to pricebook_versions | Pending |
| source_workbook_name exists | Pending |
| source_file_hash exists | Pending |
| input_row_count exists | Pending |
| output_row_count exists | Pending |
| valid_candidate_count exists | Pending |
| invalid_candidate_count exists | Pending |
| duplicate_context_count exists | Pending |
| status exists | Pending |
| status is constrained to started, success, failed | Pending |
| started_at exists | Pending |
| finished_at exists | Pending |
| error_message exists | Pending |

---

## 12. relationship_type_definitions Review

Expected purpose:

Stores allowed relationship types without hardcoding them only as a CHECK constraint.

| Check | Status |
|---|---|
| Has primary key | Pending |
| relationship_type_code exists | Pending |
| display_name exists | Pending |
| description exists | Pending |
| is_active exists | Pending |
| created_at exists | Pending |
| Initial relationship types are seeded | Pending |

Expected initial values:

```text
assembly_contains_component
cross_reference
alternate_part
```

---

## 13. part_relationships Review

Expected purpose:

Stores assembly/component and other part-to-part relationships.

| Check | Status |
|---|---|
| Has primary key | Pending |
| Has FK to pricebook_versions | Pending |
| Has parent_part_id FK to parts | Pending |
| Has child_part_id FK to parts | Pending |
| Has optional parent_pricebook_item_id FK | Pending |
| Has optional child_pricebook_item_id FK | Pending |
| Uses relationship_type_code | Pending |
| Has FK to relationship_type_definitions | Pending |
| relationship_source exists | Pending |
| source_sheet exists | Pending |
| source_row_number exists | Pending |
| confidence_level exists | Pending |
| confidence_level is constrained to derived, verified, manual | Pending |
| is_verified exists | Pending |
| parent_part_id cannot equal child_part_id | Pending |
| parent_pricebook_item_id cannot equal child_pricebook_item_id when both exist | Pending |
| Duplicate relationship context is constrained | Pending |

Important:

Relationships derived from Complete Assembly Number should be marked as:

```text
confidence_level = derived
is_verified = 0
```

They should not be presented as verified engineering BOM truth unless confirmed.

---

## 14. domain_synonyms Review

Expected purpose:

Stores general domain terminology normalization.

Examples:

```text
assy -> assembly
OD -> outside diameter
comp -> component
```

| Check | Status |
|---|---|
| Has primary key | Pending |
| term exists | Pending |
| term_normalized exists | Pending |
| canonical_term exists | Pending |
| canonical_term_normalized exists | Pending |
| scope_key exists | Pending |
| synonym_type exists | Pending |
| applies_to_tool_family exists | Pending |
| is_active exists | Pending |
| Index exists on term_normalized | Pending |
| Index exists on canonical_term_normalized | Pending |
| Active duplicate synonym rules are constrained | Pending |

Expected active uniqueness:

```text
term_normalized + canonical_term_normalized + scope_key
where is_active = 1
```

---

## 15. item_aliases Review

Expected purpose:

Stores aliases tied to specific parts or item contexts.

| Check | Status |
|---|---|
| Has primary key | Pending |
| Has optional FK to parts | Pending |
| Has optional FK to pricebook_items | Pending |
| alias_text exists | Pending |
| alias_text_normalized exists | Pending |
| alias_type exists | Pending |
| source exists | Pending |
| is_active exists | Pending |
| At least one of part_id or pricebook_item_id is required | Pending |
| Duplicate part alias is constrained using normalized alias | Pending |
| Duplicate pricebook item alias is constrained using normalized alias | Pending |

Difference:

```text
domain_synonyms = general language normalization
item_aliases = aliases tied to specific parts or item contexts
```

---

## 16. Index Review

Expected indexes:

| Index Purpose | Status |
|---|---|
| One active pricebook version per product family | Pending |
| Section lookup by version and normalized section | Pending |
| Valid candidate filtering | Pending |
| Assembly number lookup | Pending |
| Source row lookup | Pending |
| Item lookup by part_id | Pending |
| Attribute lookup by name/value | Pending |
| Parent relationship lookup | Pending |
| Child relationship lookup | Pending |
| Duplicate relationship context protection | Pending |
| Domain synonym lookup by normalized term | Pending |
| Domain synonym lookup by normalized canonical term | Pending |
| Active synonym uniqueness | Pending |
| Item alias lookup by normalized alias | Pending |
| Duplicate part alias protection | Pending |
| Duplicate pricebook item alias protection | Pending |

---

## 17. Initial Seed Data Review

Expected seeded attribute definitions:

| Attribute | Status |
|---|---|
| overshot_od | Pending |
| size | Pending |
| total_length | Pending |
| diameter_largest_wicker | Pending |
| diameter_smallest_wicker | Pending |
| catch_size | Pending |
| nominal_size_or_catch_size | Pending |
| assembly_dressed_to_packoff | Pending |
| shoe_od | Pending |
| hole_size | Pending |
| inside_diameter | Pending |

Expected seeded relationship types:

| Relationship Type | Status |
|---|---|
| assembly_contains_component | Pending |
| cross_reference | Pending |
| alternate_part | Pending |

Risk to watch:

If the DDL is run more than once, seed inserts may fail due to unique constraints. This is acceptable for first manual DDL testing, but later migrations should be migration-controlled or idempotent.

---

## 18. Known Open Questions Before Production Execution

These must be answered before production deployment:

1. Should production ingestion require source_file_hash even though the DB column allows NULL?
2. Should product_family become a lookup table later?
3. Should relationship_source become a lookup table later?
4. Should relationship confidence levels become a lookup table later?
5. Should alias_type and synonym_type become lookup tables later?
6. Should we add updated_at columns for editable configuration tables?
7. Should we add created_by or approved_by fields for manually maintained aliases/synonyms?
8. Should source workbook rows be archived as raw JSON for forensic traceability?
9. Should SQL execution be managed later by Alembic instead of manual SQL files?
10. Should first execution happen on LocalDB, SQL Server Developer Edition, or a NOV development database?

---

## 19. Final Pre-Execution Checklist

Before running this SQL anywhere:

| Check | Status |
|---|---|
| DDL reviewed manually | Pending |
| SQL file committed to GitHub | Pending |
| CI passed | Pending |
| SQL Server target environment selected | Pending |
| Database name selected | Pending |
| Backup or rollback plan defined | Pending |
| DDL executed only in local or development environment first | Pending |
| Table creation verified after execution | Pending |
| No production data touched | Pending |

---

## Review Decision

Current decision:

```text
Do not run the SQL DDL in production.
```

Next step:

Create a lightweight SQL static review script that checks whether the DDL file contains the expected schema, tables, constraints, indexes, and seed attributes.
