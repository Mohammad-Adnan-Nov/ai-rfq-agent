from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class StaticSqlCheck:
    name: str
    category: str
    required_patterns: tuple[str, ...]


@dataclass
class StaticSqlCheckResult:
    name: str
    category: str
    passed: bool
    missing_patterns: list[str]


@dataclass
class StaticSqlReviewReport:
    sql_path: str
    passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    results: list[StaticSqlCheckResult]

    def to_dict(self) -> dict:
        return asdict(self)


EXPECTED_CHECKS: tuple[StaticSqlCheck, ...] = (
    StaticSqlCheck(
        name="Creates rfq schema",
        category="schema",
        required_patterns=("CREATE SCHEMA rfq",),
    ),
    StaticSqlCheck(
        name="Uses rfq schema for pricebook_versions",
        category="tables",
        required_patterns=("CREATE TABLE rfq.pricebook_versions",),
    ),
    StaticSqlCheck(
        name="Uses rfq schema for pricebook_sections",
        category="tables",
        required_patterns=("CREATE TABLE rfq.pricebook_sections",),
    ),
    StaticSqlCheck(
        name="Uses rfq schema for parts",
        category="tables",
        required_patterns=("CREATE TABLE rfq.parts",),
    ),
    StaticSqlCheck(
        name="Uses rfq schema for pricebook_items",
        category="tables",
        required_patterns=("CREATE TABLE rfq.pricebook_items",),
    ),
    StaticSqlCheck(
        name="Uses rfq schema for attribute_definitions",
        category="tables",
        required_patterns=("CREATE TABLE rfq.attribute_definitions",),
    ),
    StaticSqlCheck(
        name="Uses rfq schema for item_attributes",
        category="tables",
        required_patterns=("CREATE TABLE rfq.item_attributes",),
    ),
    StaticSqlCheck(
        name="Uses rfq schema for item_search_index",
        category="tables",
        required_patterns=("CREATE TABLE rfq.item_search_index",),
    ),
    StaticSqlCheck(
        name="Uses rfq schema for ingestion_runs",
        category="tables",
        required_patterns=("CREATE TABLE rfq.ingestion_runs",),
    ),
    StaticSqlCheck(
        name="Uses rfq schema for relationship_type_definitions",
        category="tables",
        required_patterns=("CREATE TABLE rfq.relationship_type_definitions",),
    ),
    StaticSqlCheck(
        name="Uses rfq schema for part_relationships",
        category="tables",
        required_patterns=("CREATE TABLE rfq.part_relationships",),
    ),
    StaticSqlCheck(
        name="Uses rfq schema for domain_synonyms",
        category="tables",
        required_patterns=("CREATE TABLE rfq.domain_synonyms",),
    ),
    StaticSqlCheck(
        name="Uses rfq schema for item_aliases",
        category="tables",
        required_patterns=("CREATE TABLE rfq.item_aliases",),
    ),
    StaticSqlCheck(
        name="pricebook_versions has product_family",
        category="columns",
        required_patterns=("product_family NVARCHAR(100) NOT NULL",),
    ),
    StaticSqlCheck(
        name="pricebook_versions has source_file_hash",
        category="columns",
        required_patterns=("source_file_hash NVARCHAR(128) NULL",),
    ),
    StaticSqlCheck(
        name="pricebook_sections has normalized fields",
        category="columns",
        required_patterns=(
            "section_number_normalized NVARCHAR(50) NOT NULL",
            "sheet_number_normalized NVARCHAR(50) NOT NULL",
            "title_normalized NVARCHAR(255) NOT NULL",
        ),
    ),
    StaticSqlCheck(
        name="domain_synonyms has normalized fields",
        category="columns",
        required_patterns=(
            "term_normalized NVARCHAR(100) NOT NULL",
            "canonical_term_normalized NVARCHAR(100) NOT NULL",
            "scope_key NVARCHAR(100) NOT NULL",
        ),
    ),
    StaticSqlCheck(
        name="item_aliases has normalized alias field",
        category="columns",
        required_patterns=("alias_text_normalized NVARCHAR(255) NOT NULL",),
    ),
    StaticSqlCheck(
        name="part_relationships uses relationship type lookup",
        category="relationships",
        required_patterns=(
            "relationship_type_code NVARCHAR(100) NOT NULL",
            "FK_part_relationships_relationship_types",
            "REFERENCES rfq.relationship_type_definitions(relationship_type_code)",
        ),
    ),
    StaticSqlCheck(
        name="Part numbers are text",
        category="governance",
        required_patterns=(
            "part_number NVARCHAR(100) NOT NULL",
            "part_number_normalized NVARCHAR(100) NOT NULL",
        ),
    ),
    StaticSqlCheck(
        name="Same source row cannot be loaded twice",
        category="constraints",
        required_patterns=("UQ_pricebook_items_source_row",),
    ),
    StaticSqlCheck(
        name="One search index per pricebook item",
        category="constraints",
        required_patterns=("UQ_item_search_index_pricebook_item",),
    ),
    StaticSqlCheck(
        name="One attribute value per item and attribute",
        category="constraints",
        required_patterns=("UQ_item_attributes_item_attribute",),
    ),
    StaticSqlCheck(
        name="Ingestion status is constrained",
        category="constraints",
        required_patterns=(
            "CK_ingestion_runs_status",
            "CHECK (status IN ('started', 'success', 'failed'))",
        ),
    ),
    StaticSqlCheck(
        name="Relationship confidence is constrained",
        category="constraints",
        required_patterns=(
            "CK_part_relationships_confidence_level",
            "CHECK (confidence_level IN ('derived', 'verified', 'manual'))",
        ),
    ),
    StaticSqlCheck(
        name="Part relationship cannot self-reference",
        category="constraints",
        required_patterns=("CK_part_relationships_no_self_reference",),
    ),
    StaticSqlCheck(
        name="Part relationship cannot use same item context",
        category="constraints",
        required_patterns=("CK_part_relationships_no_same_pricebook_item",),
    ),
    StaticSqlCheck(
        name="Item alias must target part or item",
        category="constraints",
        required_patterns=("CK_item_aliases_has_target",),
    ),
    StaticSqlCheck(
        name="One active pricebook version per product family",
        category="indexes",
        required_patterns=("UX_pricebook_versions_one_active_per_family",),
    ),
    StaticSqlCheck(
        name="Active domain synonym duplicates are constrained",
        category="indexes",
        required_patterns=("UX_domain_synonyms_active_term_scope",),
    ),
    StaticSqlCheck(
        name="Duplicate normalized part aliases are constrained",
        category="indexes",
        required_patterns=("UX_item_aliases_part_alias_normalized",),
    ),
    StaticSqlCheck(
        name="Duplicate normalized item aliases are constrained",
        category="indexes",
        required_patterns=("UX_item_aliases_pricebook_item_alias_normalized",),
    ),
    StaticSqlCheck(
        name="Attribute seed values are included",
        category="seed_data",
        required_patterns=(
            "'overshot_od'",
            "'size'",
            "'total_length'",
            "'diameter_largest_wicker'",
            "'diameter_smallest_wicker'",
            "'catch_size'",
            "'nominal_size_or_catch_size'",
            "'assembly_dressed_to_packoff'",
            "'shoe_od'",
            "'hole_size'",
            "'inside_diameter'",
        ),
    ),
    StaticSqlCheck(
        name="Relationship type seed values are included",
        category="seed_data",
        required_patterns=(
            "'assembly_contains_component'",
            "'cross_reference'",
            "'alternate_part'",
        ),
    ),
)


FORBIDDEN_PATTERNS: tuple[str, ...] = (
    "CREATE TABLE dbo.",
    "REFERENCES dbo.",
    "ON dbo.",
)


def read_sql_file(sql_path: str | Path) -> str:
    path = Path(sql_path)

    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {path}")

    return path.read_text(encoding="utf-8")


def run_static_sql_review(sql_path: str | Path) -> StaticSqlReviewReport:
    sql_text = read_sql_file(sql_path)

    results: list[StaticSqlCheckResult] = []

    for check in EXPECTED_CHECKS:
        missing_patterns = [
            pattern for pattern in check.required_patterns if pattern not in sql_text
        ]

        results.append(
            StaticSqlCheckResult(
                name=check.name,
                category=check.category,
                passed=len(missing_patterns) == 0,
                missing_patterns=missing_patterns,
            )
        )

    forbidden_found = [
        pattern for pattern in FORBIDDEN_PATTERNS if pattern in sql_text
    ]

    results.append(
        StaticSqlCheckResult(
            name="Does not use dbo schema for RFQ tables",
            category="schema",
            passed=len(forbidden_found) == 0,
            missing_patterns=forbidden_found,
        )
    )

    passed_checks = sum(1 for result in results if result.passed)
    failed_checks = len(results) - passed_checks

    return StaticSqlReviewReport(
        sql_path=str(sql_path),
        passed=failed_checks == 0,
        total_checks=len(results),
        passed_checks=passed_checks,
        failed_checks=failed_checks,
        results=results,
    )
