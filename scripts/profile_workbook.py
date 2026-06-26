from __future__ import annotations

import argparse
import json
from pathlib import Path

from rfq_agent.ingestion.workbook_reader import profile_to_dict, profile_workbook


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Profile the Fishing Tools Excel pricebook workbook."
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Path to the Excel workbook file.",
    )

    parser.add_argument(
        "--output",
        default="data/processed/workbook_profile.json",
        help="Path where the workbook profile JSON report should be saved.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    profile = profile_workbook(input_path)
    profile_dict = profile_to_dict(profile)

    output_path.write_text(
        json.dumps(profile_dict, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Workbook profile created successfully.")
    print(f"Input workbook: {input_path}")
    print(f"Output report: {output_path}")
    print(f"Sheet count: {profile.sheet_count}")
    print(f"Visible sheets: {profile.visible_sheet_count}")
    print(f"Hidden sheets: {profile.hidden_sheet_count}")
    print(f"Data sheet exists: {profile.data_sheet_exists}")

    if profile.data_sheet_headers:
        print("Detected Data sheet headers:")
        for header in profile.data_sheet_headers:
            print(f"- {header}")


if __name__ == "__main__":
    main()
