from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict

from rfq_agent.db.sql_post_load_validation import (
    SqlPostLoadValidationConfig,
    validate_sql_post_load,
    write_sql_post_load_validation_report,
)


def parse_allowed_statuses(value: str) -> tuple[str, ...]:
    statuses = tuple(status.strip() for status in value.split(",") if status.strip())

    if not statuses:
        raise argparse.ArgumentTypeError("At least one ingestion status is required.")

    return statuses


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the SQL Server pricebook post-load state."
    )

    parser.add_argument("--server", default=r".\SQLEXPRESS")
    parser.add_argument("--database", default="AI_RFQ_AGENT_DEV")
    parser.add_argument("--product-family", default="Fishing Tools")
    parser.add_argument(
        "--expected-source-workbook",
        default="Fishing Tools PB 2022 (Jun) - Working File FINAL 004.xlsx",
    )
    parser.add_argument("--expected-pricebook-versions", type=int, default=1)
    parser.add_argument("--expected-pricebook-items", type=int, default=12092)
    parser.add_argument("--expected-valid-candidates", type=int, default=11138)
    parser.add_argument("--expected-invalid-candidates", type=int, default=954)
    parser.add_argument("--expected-search-index-rows", type=int, default=11138)
    parser.add_argument("--expected-ingestion-runs", type=int, default=1)
    parser.add_argument("--expected-attribute-seed-count", type=int, default=11)
    parser.add_argument("--expected-relationship-type-seed-count", type=int, default=3)
    parser.add_argument(
        "--allowed-ingestion-statuses",
        type=parse_allowed_statuses,
        default=("succeeded", "success"),
        help="Comma-separated allowed successful ingestion statuses.",
    )
    parser.add_argument(
        "--output",
        default="data/processed/sql_post_load_validation_report.json",
    )

    args = parser.parse_args()

    config = SqlPostLoadValidationConfig(
        server=args.server,
        database=args.database,
        product_family=args.product_family,
        expected_source_workbook=args.expected_source_workbook,
        expected_pricebook_versions=args.expected_pricebook_versions,
        expected_pricebook_items=args.expected_pricebook_items,
        expected_valid_candidates=args.expected_valid_candidates,
        expected_invalid_candidates=args.expected_invalid_candidates,
        expected_search_index_rows=args.expected_search_index_rows,
        expected_ingestion_runs=args.expected_ingestion_runs,
        expected_attribute_seed_count=args.expected_attribute_seed_count,
        expected_relationship_type_seed_count=args.expected_relationship_type_seed_count,
        allowed_ingestion_statuses=args.allowed_ingestion_statuses,
    )

    report = validate_sql_post_load(config=config)
    write_sql_post_load_validation_report(report=report, output_path=args.output)

    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))

    if report.passed:
        print("SQL post-load validation passed.")
        return

    print("SQL post-load validation failed.")
    sys.exit(1)


if __name__ == "__main__":
    main()
