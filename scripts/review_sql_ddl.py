from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from rfq_agent.db.sql_static_review import run_static_sql_review


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run static checks against the SQL DDL file."
    )

    parser.add_argument(
        "--sql",
        default="alembic/manual_sql/001_create_pricebook_tables.sql",
        help="Path to the SQL DDL file.",
    )

    parser.add_argument(
        "--output",
        default="data/processed/sql_static_review_report.json",
        help="Optional JSON report output path.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    report = run_static_sql_review(sql_path=args.sql)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("SQL static review completed.")
    print(f"SQL file: {args.sql}")
    print(f"Report: {args.output}")
    print(f"Total checks: {report.total_checks}")
    print(f"Passed checks: {report.passed_checks}")
    print(f"Failed checks: {report.failed_checks}")

    if report.failed_checks:
        print("")
        print("Failed checks:")
        for result in report.results:
            if not result.passed:
                print(f"- {result.name}")
                for missing_pattern in result.missing_patterns:
                    print(f"  Missing/found pattern: {missing_pattern}")

        sys.exit(1)

    print("All SQL static checks passed.")


if __name__ == "__main__":
    main()
