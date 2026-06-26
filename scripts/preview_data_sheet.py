from __future__ import annotations

import argparse
import json
from pathlib import Path

from rfq_agent.ingestion.data_sheet_parser import build_data_sheet_preview, preview_to_dict


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview the consolidated Data sheet from the Fishing Tools pricebook."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to the Excel workbook file.",
    )

    parser.add_argument(
        "--output",
        default="data/processed/data_sheet_preview.json",
        help="Path where the Data sheet preview JSON should be saved.",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of preview rows to include in the output JSON.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    preview = build_data_sheet_preview(
        workbook_path=input_path,
        sheet_name="Data",
        preview_limit=args.limit,
    )

    output_path.write_text(
        json.dumps(preview_to_dict(preview), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Data sheet preview created successfully.")
    print(f"Input workbook: {input_path}")
    print(f"Output report: {output_path}")
    print(f"Detected header row: {preview.detected_header_row_number}")
    print(f"Rows: {preview.row_count}")
    print(f"Columns: {preview.column_count}")

    if preview.required_columns_missing:
        print("Missing required columns:")
        for column in preview.required_columns_missing:
            print(f"- {column}")
    else:
        print("All required columns are present.")

    print("Important column non-empty counts:")
    for column, count in preview.important_column_non_empty_counts.items():
        print(f"- {column}: {count}")


if __name__ == "__main__":
    main()
