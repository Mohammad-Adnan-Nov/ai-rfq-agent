from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from rfq_agent.ingestion.data_sheet_parser import clean_text, read_data_sheet


ATTRIBUTE_COLUMNS = [
    "Overshot OD",
    "Size",
    "Complete Assembly Number",
    "Total Length",
    "Diameter of Largest Wicker",
    "Diameter of Smallest Wicker",
    "Catch Size",
    "Nominal Size/Nominal Catch Size",
    "Assembly dressed to packoff",
    "Shoe OD",
    "Hole Size",
    "Inside Diameter",
]

OUTPUT_COLUMNS = [
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
    "logan_part_number",
    "logan_description",
    "complete_assembly_number",
    "overshot_od",
    "size",
    "total_length",
    "catch_size",
    "nominal_size_or_catch_size",
    "shoe_od",
    "hole_size",
    "inside_diameter",
    "is_valid_candidate",
    "invalid_reason",
    "search_text",
]


@dataclass
class ItemRecordsBuildResult:
    pricebook_version: str
    source_workbook: str
    input_row_count: int
    output_row_count: int
    valid_candidate_count: int
    invalid_candidate_count: int
    duplicate_part_number_count: int
    blank_part_number_count: int
    placeholder_part_number_count: int
    invalid_reason_counts: dict[str, int]
    output_csv_path: str
    quality_report_path: str
    sample_records: list[dict[str, str]]


def normalize_part_number(value: Any) -> str:
    text = clean_text(value).upper()
    text = text.replace(" ", "")
    return text


def is_placeholder_value(value: Any) -> bool:
    normalized = normalize_part_number(value)

    placeholders = {
        "",
        "N/A",
        "NA",
        "NONE",
        "NULL",
        "-",
        "--",
        "TBD",
        "NIL",
    }

    return normalized in placeholders


def is_placeholder_part_number(value: str) -> bool:
    return is_placeholder_value(value)


def get_invalid_reason(part_number: str, description: str) -> str:
    if not clean_text(part_number):
        return "blank_part_number"

    if is_placeholder_part_number(part_number):
        return "placeholder_part_number"

    if not clean_text(description):
        return "blank_description"

    return ""


def add_search_field(parts: list[str], label: str, value: Any) -> None:
    cleaned_value = clean_text(value)

    if not cleaned_value:
        return

    if is_placeholder_value(cleaned_value):
        return

    parts.append(f"{label}: {cleaned_value}")


def build_search_text(row: dict[str, str]) -> str:
    parts: list[str] = []

    add_search_field(parts, "Part Number", row.get("part_number", ""))
    add_search_field(parts, "Description", row.get("description", ""))
    add_search_field(parts, "Title", row.get("title", ""))
    add_search_field(parts, "Section", row.get("section_number", ""))
    add_search_field(parts, "Sheet", row.get("sheet_number", ""))
    add_search_field(parts, "Logan Part Number", row.get("logan_part_number", ""))
    add_search_field(parts, "Logan Description", row.get("logan_description", ""))
    add_search_field(parts, "Complete Assembly Number", row.get("complete_assembly_number", ""))
    add_search_field(parts, "Overshot OD", row.get("overshot_od", ""))
    add_search_field(parts, "Size", row.get("size", ""))
    add_search_field(parts, "Catch Size", row.get("catch_size", ""))
    add_search_field(parts, "Nominal Size/Catch Size", row.get("nominal_size_or_catch_size", ""))
    add_search_field(parts, "Shoe OD", row.get("shoe_od", ""))
    add_search_field(parts, "Hole Size", row.get("hole_size", ""))
    add_search_field(parts, "Inside Diameter", row.get("inside_diameter", ""))

    return " | ".join(parts)


def build_item_records_dataframe(
    workbook_path: str | Path,
    pricebook_version: str,
) -> pd.DataFrame:
    workbook_path = Path(workbook_path)
    source_df, _header_row_index = read_data_sheet(workbook_path=workbook_path, sheet_name="Data")

    records: list[dict[str, str]] = []

    for _index, source_row in source_df.iterrows():
        part_number = clean_text(source_row.get("Part #", ""))
        description = clean_text(source_row.get("Description", ""))

        invalid_reason = get_invalid_reason(part_number=part_number, description=description)

        record = {
            "pricebook_version": clean_text(pricebook_version),
            "source_workbook": workbook_path.name,
            "source_sheet": clean_text(source_row.get("__source_sheet", "")),
            "source_row_number": clean_text(source_row.get("__source_row_number", "")),
            "sheet_number": clean_text(source_row.get("Sheet #", "")),
            "section_number": clean_text(source_row.get("Section #", "")),
            "title": clean_text(source_row.get("Title", "")),
            "description": description,
            "part_number": part_number,
            "part_number_normalized": normalize_part_number(part_number),
            "logan_part_number": clean_text(source_row.get("Logan Part #", "")),
            "logan_description": clean_text(source_row.get("Logan Description", "")),
            "complete_assembly_number": clean_text(source_row.get("Complete Assembly Number", "")),
            "overshot_od": clean_text(source_row.get("Overshot OD", "")),
            "size": clean_text(source_row.get("Size", "")),
            "total_length": clean_text(source_row.get("Total Length", "")),
            "catch_size": clean_text(source_row.get("Catch Size", "")),
            "nominal_size_or_catch_size": clean_text(
                source_row.get("Nominal Size/Nominal Catch Size", "")
            ),
            "shoe_od": clean_text(source_row.get("Shoe OD", "")),
            "hole_size": clean_text(source_row.get("Hole Size", "")),
            "inside_diameter": clean_text(source_row.get("Inside Diameter", "")),
            "is_valid_candidate": "false" if invalid_reason else "true",
            "invalid_reason": invalid_reason,
        }

        record["search_text"] = build_search_text(record)
        records.append(record)

    output_df = pd.DataFrame(records, columns=OUTPUT_COLUMNS)
    return output_df


def build_item_records_outputs(
    workbook_path: str | Path,
    pricebook_version: str,
    output_csv_path: str | Path,
    quality_report_path: str | Path,
    sample_limit: int = 10,
) -> ItemRecordsBuildResult:
    output_csv_path = Path(output_csv_path)
    quality_report_path = Path(quality_report_path)

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    quality_report_path.parent.mkdir(parents=True, exist_ok=True)

    records_df = build_item_records_dataframe(
        workbook_path=workbook_path,
        pricebook_version=pricebook_version,
    )

    records_df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")

    valid_candidate_count = int((records_df["is_valid_candidate"] == "true").sum())
    invalid_candidate_count = int((records_df["is_valid_candidate"] == "false").sum())
    blank_part_number_count = int((records_df["part_number"] == "").sum())
    placeholder_part_number_count = int(
        records_df["part_number"].apply(is_placeholder_part_number).sum()
    )

    invalid_reason_counts = {
        str(reason): int(count)
        for reason, count in records_df.loc[
            records_df["invalid_reason"] != "",
            "invalid_reason",
        ]
        .value_counts() # type: ignore
        .items()
    }

    duplicate_part_number_count = int(
        records_df.loc[
            records_df["part_number_normalized"] != "",
            "part_number_normalized",
        ].duplicated().sum() # type: ignore
    )

    sample_records = (
        records_df[
            [
                "source_row_number",
                "section_number",
                "title",
                "description",
                "part_number",
                "complete_assembly_number",
                "is_valid_candidate",
                "invalid_reason",
                "search_text",
            ]
        ]
        .head(sample_limit)
        .to_dict(orient="records")
    ) # type: ignore

    result = ItemRecordsBuildResult(
        pricebook_version=pricebook_version,
        source_workbook=Path(workbook_path).name,
        input_row_count=int(len(records_df)),
        output_row_count=int(len(records_df)),
        valid_candidate_count=valid_candidate_count,
        invalid_candidate_count=invalid_candidate_count,
        duplicate_part_number_count=duplicate_part_number_count,
        blank_part_number_count=blank_part_number_count,
        placeholder_part_number_count=placeholder_part_number_count,
        invalid_reason_counts=invalid_reason_counts,
        output_csv_path=str(output_csv_path),
        quality_report_path=str(quality_report_path),
        sample_records=sample_records,
    )

    quality_report_path.write_text(
        json.dumps(asdict(result), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return result
