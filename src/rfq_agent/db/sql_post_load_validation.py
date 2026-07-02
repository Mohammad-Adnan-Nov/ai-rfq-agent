from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from rfq_agent.db.sql_connection import connect_sql_server


@dataclass(frozen=True)
class SqlPostLoadValidationConfig:
    server: str
    database: str
    product_family: str
    expected_source_workbook: str
    expected_pricebook_versions: int = 1
    expected_pricebook_items: int = 12092
    expected_valid_candidates: int = 11138
    expected_invalid_candidates: int = 954
    expected_search_index_rows: int = 11138
    expected_ingestion_runs: int = 1
    expected_attribute_seed_count: int = 11
    expected_relationship_type_seed_count: int = 3
    allowed_ingestion_statuses: tuple[str, ...] = ("succeeded", "success")


@dataclass(frozen=True)
class SqlPostLoadMetrics:
    pricebook_versions_count: int
    pricebook_sections_count: int
    parts_count: int
    pricebook_items_count: int
    item_attributes_count: int
    item_search_index_count: int
    ingestion_runs_count: int
    attribute_seed_count: int
    relationship_type_seed_count: int
    valid_candidate_count: int
    invalid_candidate_count: int
    invalid_rows_in_search_index_count: int
    missing_traceability_count: int
    source_workbook_mismatch_count: int
    active_pricebook_version_count: int
    ingestion_run_summary_match_count: int
    ingestion_statuses: list[str]


@dataclass(frozen=True)
class SqlValidationCheck:
    check_name: str
    passed: bool
    expected: str
    actual: str
    details: str = ""


@dataclass(frozen=True)
class SqlPostLoadValidationReport:
    server: str
    database: str
    passed: bool
    metrics: SqlPostLoadMetrics
    checks: list[SqlValidationCheck]


def _scalar_int(cursor: Any, sql: str, params: tuple[Any, ...] = ()) -> int:
    cursor.execute(sql, *params)
    row = cursor.fetchone()

    if row is None:
        return 0

    return int(row[0])


def _string_list(cursor: Any, sql: str) -> list[str]:
    cursor.execute(sql)
    return [str(row[0]) for row in cursor.fetchall()]


def collect_sql_post_load_metrics(
    cursor: Any,
    config: SqlPostLoadValidationConfig,
) -> SqlPostLoadMetrics:
    pricebook_versions_count = _scalar_int(
        cursor,
        "SELECT COUNT(*) FROM rfq.pricebook_versions;",
    )
    pricebook_sections_count = _scalar_int(
        cursor,
        "SELECT COUNT(*) FROM rfq.pricebook_sections;",
    )
    parts_count = _scalar_int(
        cursor,
        "SELECT COUNT(*) FROM rfq.parts;",
    )
    pricebook_items_count = _scalar_int(
        cursor,
        "SELECT COUNT(*) FROM rfq.pricebook_items;",
    )
    item_attributes_count = _scalar_int(
        cursor,
        "SELECT COUNT(*) FROM rfq.item_attributes;",
    )
    item_search_index_count = _scalar_int(
        cursor,
        "SELECT COUNT(*) FROM rfq.item_search_index;",
    )
    ingestion_runs_count = _scalar_int(
        cursor,
        "SELECT COUNT(*) FROM rfq.ingestion_runs;",
    )
    attribute_seed_count = _scalar_int(
        cursor,
        "SELECT COUNT(*) FROM rfq.attribute_definitions;",
    )
    relationship_type_seed_count = _scalar_int(
        cursor,
        "SELECT COUNT(*) FROM rfq.relationship_type_definitions;",
    )
    valid_candidate_count = _scalar_int(
        cursor,
        """
        SELECT COUNT(*)
        FROM rfq.pricebook_items
        WHERE is_valid_candidate = 1;
        """,
    )
    invalid_candidate_count = _scalar_int(
        cursor,
        """
        SELECT COUNT(*)
        FROM rfq.pricebook_items
        WHERE is_valid_candidate = 0;
        """,
    )
    invalid_rows_in_search_index_count = _scalar_int(
        cursor,
        """
        SELECT COUNT(*)
        FROM rfq.item_search_index si
        JOIN rfq.pricebook_items pi
            ON pi.pricebook_item_id = si.pricebook_item_id
        WHERE pi.is_valid_candidate = 0;
        """,
    )
    missing_traceability_count = _scalar_int(
        cursor,
        """
        SELECT COUNT(*)
        FROM rfq.pricebook_items
        WHERE source_workbook IS NULL
           OR LTRIM(RTRIM(source_workbook)) = ''
           OR source_sheet IS NULL
           OR LTRIM(RTRIM(source_sheet)) = ''
           OR source_row_number IS NULL;
        """,
    )
    source_workbook_mismatch_count = _scalar_int(
        cursor,
        """
        SELECT COUNT(*)
        FROM rfq.pricebook_items
        WHERE source_workbook <> ?;
        """,
        (config.expected_source_workbook,),
    )
    active_pricebook_version_count = _scalar_int(
        cursor,
        """
        SELECT COUNT(*)
        FROM rfq.pricebook_versions
        WHERE product_family = ?
          AND is_active = 1;
        """,
        (config.product_family,),
    )
    ingestion_run_summary_match_count = _scalar_int(
        cursor,
        """
        SELECT COUNT(*)
        FROM rfq.ingestion_runs
        WHERE input_row_count = ?
          AND output_row_count = ?
          AND valid_candidate_count = ?
          AND invalid_candidate_count = ?;
        """,
        (
            config.expected_pricebook_items,
            config.expected_pricebook_items,
            config.expected_valid_candidates,
            config.expected_invalid_candidates,
        ),
    )
    ingestion_statuses = _string_list(
        cursor,
        """
        SELECT DISTINCT status
        FROM rfq.ingestion_runs
        ORDER BY status;
        """,
    )

    return SqlPostLoadMetrics(
        pricebook_versions_count=pricebook_versions_count,
        pricebook_sections_count=pricebook_sections_count,
        parts_count=parts_count,
        pricebook_items_count=pricebook_items_count,
        item_attributes_count=item_attributes_count,
        item_search_index_count=item_search_index_count,
        ingestion_runs_count=ingestion_runs_count,
        attribute_seed_count=attribute_seed_count,
        relationship_type_seed_count=relationship_type_seed_count,
        valid_candidate_count=valid_candidate_count,
        invalid_candidate_count=invalid_candidate_count,
        invalid_rows_in_search_index_count=invalid_rows_in_search_index_count,
        missing_traceability_count=missing_traceability_count,
        source_workbook_mismatch_count=source_workbook_mismatch_count,
        active_pricebook_version_count=active_pricebook_version_count,
        ingestion_run_summary_match_count=ingestion_run_summary_match_count,
        ingestion_statuses=ingestion_statuses,
    )


def _check_equal(
    check_name: str,
    actual: int,
    expected: int,
    details: str = "",
) -> SqlValidationCheck:
    return SqlValidationCheck(
        check_name=check_name,
        passed=actual == expected,
        expected=str(expected),
        actual=str(actual),
        details=details,
    )


def _check_zero(
    check_name: str,
    actual: int,
    details: str = "",
) -> SqlValidationCheck:
    return _check_equal(
        check_name=check_name,
        actual=actual,
        expected=0,
        details=details,
    )


def _check_greater_than_zero(
    check_name: str,
    actual: int,
    details: str = "",
) -> SqlValidationCheck:
    return SqlValidationCheck(
        check_name=check_name,
        passed=actual > 0,
        expected="> 0",
        actual=str(actual),
        details=details,
    )


def validate_sql_post_load_metrics(
    metrics: SqlPostLoadMetrics,
    config: SqlPostLoadValidationConfig,
) -> list[SqlValidationCheck]:
    checks = [
        _check_equal(
            "pricebook_versions_count",
            metrics.pricebook_versions_count,
            config.expected_pricebook_versions,
        ),
        _check_greater_than_zero(
            "pricebook_sections_count",
            metrics.pricebook_sections_count,
        ),
        _check_greater_than_zero(
            "parts_count",
            metrics.parts_count,
        ),
        _check_equal(
            "pricebook_items_count",
            metrics.pricebook_items_count,
            config.expected_pricebook_items,
        ),
        _check_greater_than_zero(
            "item_attributes_count",
            metrics.item_attributes_count,
        ),
        _check_equal(
            "item_search_index_count",
            metrics.item_search_index_count,
            config.expected_search_index_rows,
        ),
        _check_equal(
            "ingestion_runs_count",
            metrics.ingestion_runs_count,
            config.expected_ingestion_runs,
        ),
        _check_equal(
            "attribute_seed_count",
            metrics.attribute_seed_count,
            config.expected_attribute_seed_count,
        ),
        _check_equal(
            "relationship_type_seed_count",
            metrics.relationship_type_seed_count,
            config.expected_relationship_type_seed_count,
        ),
        _check_equal(
            "valid_candidate_count",
            metrics.valid_candidate_count,
            config.expected_valid_candidates,
        ),
        _check_equal(
            "invalid_candidate_count",
            metrics.invalid_candidate_count,
            config.expected_invalid_candidates,
        ),
        _check_zero(
            "invalid_rows_in_search_index_count",
            metrics.invalid_rows_in_search_index_count,
            "Invalid rows should remain auditable but not searchable.",
        ),
        _check_zero(
            "missing_traceability_count",
            metrics.missing_traceability_count,
            "Every item must retain workbook, sheet, and source row traceability.",
        ),
        _check_zero(
            "source_workbook_mismatch_count",
            metrics.source_workbook_mismatch_count,
            "Every loaded item should come from the expected workbook.",
        ),
        _check_equal(
            "active_pricebook_version_count",
            metrics.active_pricebook_version_count,
            1,
        ),
        _check_equal(
            "ingestion_run_summary_match_count",
            metrics.ingestion_run_summary_match_count,
            1,
        ),
    ]

    actual_statuses = set(metrics.ingestion_statuses)
    allowed_statuses = set(config.allowed_ingestion_statuses)

    checks.append(
        SqlValidationCheck(
            check_name="ingestion_statuses_allowed",
            passed=bool(actual_statuses) and actual_statuses.issubset(allowed_statuses),
            expected=", ".join(sorted(allowed_statuses)),
            actual=", ".join(sorted(actual_statuses)),
            details="Statuses must match the DDL-approved successful status values.",
        )
    )

    return checks


def validate_sql_post_load(
    config: SqlPostLoadValidationConfig,
) -> SqlPostLoadValidationReport:
    connection = connect_sql_server(
        server=config.server,
        database=config.database,
    )

    try:
        cursor = connection.cursor()
        metrics = collect_sql_post_load_metrics(cursor=cursor, config=config)
        checks = validate_sql_post_load_metrics(metrics=metrics, config=config)
        passed = all(check.passed for check in checks)

        return SqlPostLoadValidationReport(
            server=config.server,
            database=config.database,
            passed=passed,
            metrics=metrics,
            checks=checks,
        )

    finally:
        connection.close()


def write_sql_post_load_validation_report(
    report: SqlPostLoadValidationReport,
    output_path: str | Path,
) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
