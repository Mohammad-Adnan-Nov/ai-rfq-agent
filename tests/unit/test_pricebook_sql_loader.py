from __future__ import annotations

import pandas as pd

from rfq_agent.db.pricebook_sql_loader import prepare_pricebook_load
from rfq_agent.ingestion.item_record_builder import OUTPUT_COLUMNS
from rfq_agent.db.pricebook_sql_loader import INGESTION_STATUS_COMPLETED


def make_row(**overrides: str) -> dict[str, str]:
    row = {column: "" for column in OUTPUT_COLUMNS}
    row.update(
        {
            "pricebook_version": "Fishing Tools PB 2022 Jun - Working File FINAL 004",
            "source_workbook": "Fishing Tools PB 2022 (Jun) - Working File FINAL 004.xlsx",
            "source_sheet": "Data",
            "source_row_number": "2",
            "sheet_number": "1",
            "section_number": "1000",
            "title": "Test Section",
            "description": "Test Part",
            "part_number": "ABC 123",
            "part_number_normalized": "ABC123",
            "is_valid_candidate": "true",
            "invalid_reason": "",
            "search_text": "Part Number: ABC 123 | Description: Test Part",
        }
    )
    row.update(overrides)
    return row


def test_prepare_pricebook_load_preserves_duplicate_contexts() -> None:
    df = pd.DataFrame(
        [
            make_row(source_row_number="2", description="Context One"),
            make_row(source_row_number="3", description="Context Two"),
        ],
        columns=OUTPUT_COLUMNS,
    )

    prepared = prepare_pricebook_load(df)

    assert len(prepared.parts) == 1
    assert len(prepared.items) == 2
    assert prepared.valid_candidate_count == 2
    assert prepared.invalid_candidate_count == 0
    assert prepared.duplicate_valid_part_context_count == 1


def test_prepare_pricebook_load_excludes_invalid_rows_from_search_index() -> None:
    df = pd.DataFrame(
        [
            make_row(source_row_number="2", is_valid_candidate="true"),
            make_row(
                source_row_number="3",
                part_number="N/A",
                part_number_normalized="N/A",
                is_valid_candidate="false",
                invalid_reason="placeholder_part_number",
                search_text="Description: Placeholder row",
            ),
        ],
        columns=OUTPUT_COLUMNS,
    )

    prepared = prepare_pricebook_load(df)

    assert len(prepared.items) == 2
    assert prepared.valid_candidate_count == 1
    assert prepared.invalid_candidate_count == 1
    assert len(prepared.search_rows) == 1


def test_prepare_pricebook_load_prepares_attribute_rows() -> None:
    df = pd.DataFrame(
        [
            make_row(
                source_row_number="2",
                overshot_od='5 7/8"',
                inside_diameter='2"',
            )
        ],
        columns=OUTPUT_COLUMNS,
    )

    prepared = prepare_pricebook_load(df)

    assert len(prepared.attributes) == 2

    attribute_names = {attribute["attribute_name"] for attribute in prepared.attributes}

    assert attribute_names == {"overshot_od", "inside_diameter"}

def test_ingestion_completed_status_matches_expected_database_value() -> None:
    assert INGESTION_STATUS_COMPLETED in {"succeeded", "success"}

