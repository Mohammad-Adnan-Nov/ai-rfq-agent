from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from rfq_agent.db.pricebook_sql_loader import (
    PricebookSqlLoadConfig,
    load_pricebook_to_sql,
    write_report,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load canonical pricebook item records into SQL Server."
    )

    parser.add_argument("--server", default=r".\SQLEXPRESS")
    parser.add_argument("--database", default="AI_RFQ_AGENT_DEV")
    parser.add_argument("--input-csv", required=True)
    parser.add_argument("--source-workbook", required=True)
    parser.add_argument("--product-family", default="Fishing Tools")
    parser.add_argument(
        "--version-code",
        default="fishing_tools_pb_2022_jun_working_file_final_004",
    )
    parser.add_argument(
        "--version-name",
        default="Fishing Tools PB 2022 Jun - Working File FINAL 004",
    )
    parser.add_argument("--search-text-version", default="v1")
    parser.add_argument(
        "--report-output",
        default="data/processed/sql_pricebook_load_report.json",
    )
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    config = PricebookSqlLoadConfig(
        server=args.server,
        database=args.database,
        input_csv=Path(args.input_csv),
        source_workbook=Path(args.source_workbook),
        product_family=args.product_family,
        version_code=args.version_code,
        version_name=args.version_name,
        search_text_version=args.search_text_version,
    )

    report = load_pricebook_to_sql(config=config, dry_run=args.dry_run)
    write_report(report, args.report_output)

    print(json.dumps(asdict(report), indent=2, ensure_ascii=False))

    if args.dry_run:
        print("Dry run completed. No SQL rows were inserted.")
    else:
        print("SQL load completed successfully.")


if __name__ == "__main__":
    main()
