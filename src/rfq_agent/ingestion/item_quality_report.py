from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd


def read_item_records_csv(csv_path: str | Path) -> pd.DataFrame:
    path = Path(csv_path)

    if not path.exists():
        raise FileNotFoundError(f"Item records CSV not found: {path}")

    return pd.read_csv(path, dtype=str, keep_default_na=False)


def get_top_counts(df: pd.DataFrame, column: str, limit: int = 20) -> list[dict[str, Any]]:
    if column not in df.columns:
        return []

    counts = Counter(value for value in df[column].tolist() if str(value).strip())

    return [
        {"value": value, "count": count}
        for value, count in counts.most_common(limit)
    ]


def get_duplicate_part_number_samples(
    df: pd.DataFrame,
    limit: int = 25,
) -> list[dict[str, Any]]:
    if "part_number_normalized" not in df.columns:
        return []

    valid_df = df[df["part_number_normalized"].str.strip() != ""].copy()

    duplicate_values = (
        valid_df["part_number_normalized"]
        .value_counts()
        .loc[lambda series: series > 1]
        .head(limit)
        .index
        .tolist()
    )

    samples: list[dict[str, Any]] = []

    for part_number_normalized in duplicate_values:
        rows = valid_df[valid_df["part_number_normalized"] == part_number_normalized]

        samples.append(
            {
                "part_number_normalized": part_number_normalized,
                "context_count": int(len(rows)),
                "examples": rows[
                    [
                        "source_row_number",
                        "section_number",
                        "title",
                        "description",
                        "part_number",
                        "complete_assembly_number",
                    ]
                ]
                .head(5)
                .to_dict(orient="records"),
            }
        )

    return samples


def get_invalid_row_samples(
    df: pd.DataFrame,
    limit: int = 25,
) -> list[dict[str, str]]:
    if "is_valid_candidate" not in df.columns:
        return []

    invalid_df = df[df["is_valid_candidate"] == "false"].copy()

    sample_columns = [
        "source_row_number",
        "section_number",
        "title",
        "description",
        "part_number",
        "invalid_reason",
        "search_text",
    ]

    available_columns = [column for column in sample_columns if column in invalid_df.columns]

    return invalid_df[available_columns].head(limit).to_dict(orient="records")


def build_item_quality_report(
    csv_path: str | Path,
    output_path: str | Path,
) -> dict[str, Any]:
    df = read_item_records_csv(csv_path)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    required_columns = [
        "pricebook_version",
        "source_workbook",
        "source_sheet",
        "source_row_number",
        "sheet_number",
        "section_number",
        "title",
        "description",
        "part_number",
        "part_number_normalized",
        "is_valid_candidate",
        "invalid_reason",
        "search_text",
    ]

    missing_required_columns = [
        column for column in required_columns if column not in df.columns
    ]

    valid_df = df[df["is_valid_candidate"] == "true"].copy()
    invalid_df = df[df["is_valid_candidate"] == "false"].copy()

    unique_part_count = int(
        valid_df.loc[
            valid_df["part_number_normalized"].str.strip() != "",
            "part_number_normalized",
        ].nunique()
    )

    duplicate_context_count = int(
        valid_df.loc[
            valid_df["part_number_normalized"].str.strip() != "",
            "part_number_normalized",
        ].duplicated().sum()
    )

    empty_search_text_count = int((df["search_text"].str.strip() == "").sum())

    report = {
        "csv_path": str(csv_path),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "valid_candidate_count": int(len(valid_df)),
        "invalid_candidate_count": int(len(invalid_df)),
        "unique_valid_part_number_count": unique_part_count,
        "duplicate_valid_part_context_count": duplicate_context_count,
        "empty_search_text_count": empty_search_text_count,
        "missing_required_columns": missing_required_columns,
        "invalid_reason_counts": get_top_counts(df, "invalid_reason", limit=20),
        "top_sections_by_row_count": get_top_counts(df, "section_number", limit=20),
        "top_titles_by_row_count": get_top_counts(df, "title", limit=20),
        "duplicate_part_number_samples": get_duplicate_part_number_samples(df, limit=25),
        "invalid_row_samples": get_invalid_row_samples(df, limit=25),
    }

    output_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return report
