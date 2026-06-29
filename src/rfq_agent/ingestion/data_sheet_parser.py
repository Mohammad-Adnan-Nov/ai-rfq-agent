from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd


IMPORTANT_COLUMNS = [
    "Sheet #",
    "Section #",
    "Title",
    "Description",
    "Part #",
    "Logan Part #",
    "Logan Description",
    "Size",
    "Complete Assembly Number",
    "Overshot OD",
    "Total Length",
    "Catch Size",
    "Nominal Size/Nominal Catch Size",
    "Shoe OD",
    "Hole Size",
    "Inside Diameter",
]

REQUIRED_COLUMNS = [
    "Sheet #",
    "Section #",
    "Title",
    "Description",
    "Part #",
]


@dataclass
class DataSheetPreview:
    workbook_path: str
    sheet_name: str
    detected_header_row_number: int
    row_count: int
    column_count: int
    columns: list[str]
    required_columns_present: list[str]
    required_columns_missing: list[str]
    important_column_non_empty_counts: dict[str, int]
    preview_rows: list[dict[str, str]]


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    text = str(value).strip()

    if text.lower() in {"nan", "none"}:
        return ""

    return " ".join(text.split())


def make_unique_column_names(column_names: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    unique_names: list[str] = []

    for index, column_name in enumerate(column_names, start=1):
        cleaned_name = clean_text(column_name)

        if not cleaned_name:
            cleaned_name = f"Unnamed Column {index}"

        if cleaned_name not in seen:
            seen[cleaned_name] = 0
            unique_names.append(cleaned_name)
            continue

        seen[cleaned_name] += 1
        unique_names.append(f"{cleaned_name}__{seen[cleaned_name]}")

    return unique_names


def detect_header_row(
    workbook_path: str | Path,
    sheet_name: str = "Data",
    max_scan_rows: int = 25,
) -> int:
    """
    Detect the header row in the Data sheet.

    Returns a zero-based row index for pandas.
    """
    preview_df = pd.read_excel(
        workbook_path,
        sheet_name=sheet_name,
        header=None,
        nrows=max_scan_rows,
        dtype=str,
        keep_default_na=False,
        engine="openpyxl",
    )

    best_row_index = 0
    best_score = -1

    for row_index, row in preview_df.iterrows():
        values = [clean_text(value) for value in row.tolist()]
        non_empty_values = [value for value in values if value]

        required_hits = sum(1 for column in REQUIRED_COLUMNS if column in non_empty_values)
        important_hits = sum(1 for column in IMPORTANT_COLUMNS if column in non_empty_values)

        score = len(non_empty_values) + (required_hits * 10) + (important_hits * 3)

        if score > best_score:
            best_score = score
            best_row_index = int(row_index) # type: ignore

    return best_row_index


def read_data_sheet(
    workbook_path: str | Path,
    sheet_name: str = "Data",
) -> tuple[pd.DataFrame, int]:
    """
    Read the Data sheet while forcing every value to string.

    This is important because part numbers must not be converted into numbers.
    """
    header_row_index = detect_header_row(workbook_path=workbook_path, sheet_name=sheet_name)

    df = pd.read_excel(
        workbook_path,
        sheet_name=sheet_name,
        header=header_row_index,
        dtype=str,
        keep_default_na=False,
        engine="openpyxl",
    )

    df.columns = make_unique_column_names([str(column) for column in df.columns])

    df = df.map(clean_text)

    non_source_columns = list(df.columns)
    df = df[df[non_source_columns].apply(lambda row: any(value for value in row), axis=1)].copy()

    first_data_excel_row_number = header_row_index + 2
    df.insert(0, "__source_sheet", sheet_name)
    df.insert(
        1,
        "__source_row_number",
        [str(first_data_excel_row_number + row_index) for row_index in range(len(df))],
    )

    return df, header_row_index # type: ignore


def build_data_sheet_preview(
    workbook_path: str | Path,
    sheet_name: str = "Data",
    preview_limit: int = 10,
) -> DataSheetPreview:
    df, header_row_index = read_data_sheet(workbook_path=workbook_path, sheet_name=sheet_name)

    columns = list(df.columns)

    required_columns_present = [column for column in REQUIRED_COLUMNS if column in columns]
    required_columns_missing = [column for column in REQUIRED_COLUMNS if column not in columns]

    important_column_non_empty_counts: dict[str, int] = {}

    for column in IMPORTANT_COLUMNS:
        if column in df.columns:
            important_column_non_empty_counts[column] = int((df[column] != "").sum())

    preview_columns = [
        "__source_sheet",
        "__source_row_number",
        "Sheet #",
        "Section #",
        "Title",
        "Description",
        "Part #",
        "Logan Part #",
        "Logan Description",
        "Size",
        "Complete Assembly Number",
    ]

    available_preview_columns = [column for column in preview_columns if column in df.columns]
    preview_rows = (
        df[available_preview_columns]
        .head(preview_limit)
        .to_dict(orient="records")
    ) # type: ignore

    return DataSheetPreview(
        workbook_path=str(workbook_path),
        sheet_name=sheet_name,
        detected_header_row_number=header_row_index + 1,
        row_count=int(len(df)),
        column_count=int(len(df.columns)),
        columns=columns,
        required_columns_present=required_columns_present,
        required_columns_missing=required_columns_missing,
        important_column_non_empty_counts=important_column_non_empty_counts,
        preview_rows=preview_rows, # type: ignore
    )


def preview_to_dict(preview: DataSheetPreview) -> dict[str, Any]:
    return asdict(preview)
