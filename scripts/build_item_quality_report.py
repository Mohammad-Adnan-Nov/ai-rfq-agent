from __future__ import annotations

import argparse

from rfq_agent.ingestion.item_quality_report import build_item_quality_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a stronger data quality report from extracted item records."
    )

    parser.add_argument(
        "--input-csv",
        required=True,
        help="Path to the extracted item records CSV.",
    )

    parser.add_argument(
        "--output",
        default="data/processed/item_quality_report.json",
        help="Path where the quality report JSON should be saved.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    report = build_item_quality_report(
        csv_path=args.input_csv,
        output_path=args.output,
    )

    print("Item quality report created successfully.")
    print(f"Input CSV: {args.input_csv}")
    print(f"Output report: {args.output}")
    print(f"Rows: {report['row_count']}")
    print(f"Columns: {report['column_count']}")
    print(f"Valid candidates: {report['valid_candidate_count']}")
    print(f"Invalid candidates: {report['invalid_candidate_count']}")
    print(f"Unique valid part numbers: {report['unique_valid_part_number_count']}")
    print(f"Duplicate valid part contexts: {report['duplicate_valid_part_context_count']}")
    print(f"Empty search_text count: {report['empty_search_text_count']}")

    if report["missing_required_columns"]:
        print("Missing required columns:")
        for column in report["missing_required_columns"]:
            print(f"- {column}")
    else:
        print("All required columns are present.")


if __name__ == "__main__":
    main()
