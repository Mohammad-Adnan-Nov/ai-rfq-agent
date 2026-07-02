from __future__ import annotations

from rfq_agent.db.sql_post_load_validation import (
    SqlPostLoadMetrics,
    SqlPostLoadValidationConfig,
    validate_sql_post_load_metrics,
)


def make_config() -> SqlPostLoadValidationConfig:
    return SqlPostLoadValidationConfig(
        server=r".\SQLEXPRESS",
        database="AI_RFQ_AGENT_DEV",
        product_family="Fishing Tools",
        expected_source_workbook=(
            "Fishing Tools PB 2022 (Jun) - Working File FINAL 004.xlsx"
        ),
    )


def make_valid_metrics() -> SqlPostLoadMetrics:
    return SqlPostLoadMetrics(
        pricebook_versions_count=1,
        pricebook_sections_count=100,
        parts_count=6000,
        pricebook_items_count=12092,
        item_attributes_count=1000,
        item_search_index_count=11138,
        ingestion_runs_count=1,
        attribute_seed_count=11,
        relationship_type_seed_count=3,
        valid_candidate_count=11138,
        invalid_candidate_count=954,
        invalid_rows_in_search_index_count=0,
        missing_traceability_count=0,
        source_workbook_mismatch_count=0,
        active_pricebook_version_count=1,
        ingestion_run_summary_match_count=1,
        ingestion_statuses=["succeeded"],
    )


def test_validate_sql_post_load_metrics_passes_for_expected_counts() -> None:
    checks = validate_sql_post_load_metrics(
        metrics=make_valid_metrics(),
        config=make_config(),
    )

    assert all(check.passed for check in checks)


def test_validate_sql_post_load_metrics_fails_for_wrong_item_count() -> None:
    metrics = make_valid_metrics()
    bad_metrics = SqlPostLoadMetrics(
        **{
            **metrics.__dict__,
            "pricebook_items_count": 12091,
        }
    )

    checks = validate_sql_post_load_metrics(
        metrics=bad_metrics,
        config=make_config(),
    )

    failed_checks = [check.check_name for check in checks if not check.passed]

    assert "pricebook_items_count" in failed_checks


def test_validate_sql_post_load_metrics_fails_if_invalid_rows_are_searchable() -> None:
    metrics = make_valid_metrics()
    bad_metrics = SqlPostLoadMetrics(
        **{
            **metrics.__dict__,
            "invalid_rows_in_search_index_count": 1,
        }
    )

    checks = validate_sql_post_load_metrics(
        metrics=bad_metrics,
        config=make_config(),
    )

    failed_checks = [check.check_name for check in checks if not check.passed]

    assert "invalid_rows_in_search_index_count" in failed_checks


def test_validate_sql_post_load_metrics_fails_for_unexpected_status() -> None:
    metrics = make_valid_metrics()
    bad_metrics = SqlPostLoadMetrics(
        **{
            **metrics.__dict__,
            "ingestion_statuses": ["failed"],
        }
    )

    checks = validate_sql_post_load_metrics(
        metrics=bad_metrics,
        config=make_config(),
    )

    failed_checks = [check.check_name for check in checks if not check.passed]

    assert "ingestion_statuses_allowed" in failed_checks
