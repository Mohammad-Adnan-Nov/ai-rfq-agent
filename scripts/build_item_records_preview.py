from __future__ import annotations

import argparse

from rfq_agent.ingestion.item_record_builder import build_item_records_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build SQL-ready item record preview files from the Data sheet."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to the Excel workbook file.",
    )

    parser.add_argument(
        "--pricebook-version",
        required=True,
        help="Human-readable pricebook version label.",
    )

    parser.add_argument(
        "--output-csv",
        default="data/processed/pricebook_items_preview.csv",
        help="Path where the extracted item preview CSV should be saved.",
    )

    parser.add_argument(
        "--quality-report",
        default="data/processed/pricebook_items_quality_report.json",
        help="Path where the quality report JSON should be saved.",
    )

    parser.add_argument(
        "--sample-limit",
        type=int,
        default=10,
        help="Number of sample records to include in the quality report.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    result = build_item_records_outputs(
        workbook_path=args.input,
        pricebook_version=args.pricebook_version,
        output_csv_path=args.output_csv,
        quality_report_path=args.quality_report,
        sample_limit=args.sample_limit,
    )

    print("Item records preview created successfully.")
    print(f"Pricebook version: {result.pricebook_version}")
    print(f"Source workbook: {result.source_workbook}")
    print(f"Output CSV: {result.output_csv_path}")
    print(f"Quality report: {result.quality_report_path}")
    print(f"Output rows: {result.output_row_count}")
    print(f"Valid candidates: {result.valid_candidate_count}")
    print(f"Invalid candidates: {result.invalid_candidate_count}")
    print(f"Blank part numbers: {result.blank_part_number_count}")
    print(f"Placeholder part numbers: {result.placeholder_part_number_count}")
    print(f"Duplicate part-number contexts: {result.duplicate_part_number_count}")


if __name__ == "__main__":
    main()
