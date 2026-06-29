from pathlib import Path

import pandas as pd

from rfq_agent.ingestion.item_record_builder import (
    build_item_records_dataframe,
    build_search_text,
    get_invalid_reason,
    is_placeholder_part_number,
    normalize_part_number,
)


def test_normalize_part_number_keeps_text_format():
    assert normalize_part_number("  abc-123 ") == "ABC-123"
    assert normalize_part_number(" 97 90 ") == "9790"


def test_placeholder_part_numbers_are_detected():
    assert is_placeholder_part_number("N/A")
    assert is_placeholder_part_number("NA")
    assert is_placeholder_part_number("-")
    assert is_placeholder_part_number("")
    assert not is_placeholder_part_number("9790")


def test_invalid_reason_detection():
    assert get_invalid_reason("", "Top Sub") == "blank_part_number"
    assert get_invalid_reason("N/A", "Top Sub") == "placeholder_part_number"
    assert get_invalid_reason("9790", "") == "blank_description"
    assert get_invalid_reason("9790", "Complete Assembly") == ""


def test_search_text_excludes_placeholder_values():
    row = {
        "part_number": "9790",
        "description": "Complete Assembly",
        "title": "Series 10",
        "section_number": "1010",
        "sheet_number": "1",
        "logan_part_number": "N/A",
        "logan_description": "",
        "complete_assembly_number": "9790",
        "overshot_od": "1.5625",
    }

    search_text = build_search_text(row)

    assert "Part Number: 9790" in search_text
    assert "Description: Complete Assembly" in search_text
    assert "Complete Assembly Number: 9790" in search_text
    assert "Logan Part Number: N/A" not in search_text


def test_search_text_includes_technical_attributes():
    row = {
        "part_number": "12345",
        "description": "Sample Grapple",
        "title": "Sample Tool",
        "section_number": "2000",
        "sheet_number": "10",
        "total_length": "12.50",
        "diameter_largest_wicker": "5.25",
        "diameter_smallest_wicker": "4.75",
        "catch_size": "5",
        "nominal_size_or_catch_size": "5 7/8",
        "assembly_dressed_to_packoff": "Yes",
        "shoe_od": "6.125",
        "hole_size": "8.5",
        "inside_diameter": "3.25",
    }

    search_text = build_search_text(row)

    assert "Total Length: 12.50" in search_text
    assert "Diameter of Largest Wicker: 5.25" in search_text
    assert "Diameter of Smallest Wicker: 4.75" in search_text
    assert "Catch Size: 5" in search_text
    assert "Nominal Size/Catch Size: 5 7/8" in search_text
    assert "Assembly Dressed to Packoff: Yes" in search_text
    assert "Shoe OD: 6.125" in search_text
    assert "Hole Size: 8.5" in search_text
    assert "Inside Diameter: 3.25" in search_text


def test_build_item_records_dataframe_from_sample_workbook(tmp_path: Path):
    workbook_path = tmp_path / "sample_pricebook.xlsx"

    sample_data = pd.DataFrame(
        [
            {
                "Sheet #": "1",
                "Section #": "1010",
                "Title": "Series 10",
                "Description": "Complete Assembly",
                "Overshot OD": "1.5625",
                "Part #": "9790",
                "Logan Part #": "N/A",
                "Logan Description": "",
                "Size": "",
                "Complete Assembly Number": "9790",
                "Total Length": "10.5",
                "Diameter of Largest Wicker": "5.25",
                "Diameter of Smallest Wicker": "4.75",
                "Catch Size": "5",
                "Nominal Size/Nominal Catch Size": "5 7/8",
                "Assembly dressed to packoff": "Yes",
                "Shoe OD": "6.125",
                "Hole Size": "8.5",
                "Inside Diameter": "3.25",
            },
            {
                "Sheet #": "1",
                "Section #": "1010",
                "Title": "Series 10",
                "Description": "Top Sub",
                "Overshot OD": "1.5625",
                "Part #": "9791",
                "Logan Part #": "N/A",
                "Logan Description": "",
                "Size": "",
                "Complete Assembly Number": "9790",
                "Total Length": "",
                "Diameter of Largest Wicker": "",
                "Diameter of Smallest Wicker": "",
                "Catch Size": "",
                "Nominal Size/Nominal Catch Size": "",
                "Assembly dressed to packoff": "",
                "Shoe OD": "",
                "Hole Size": "",
                "Inside Diameter": "",
            },
            {
                "Sheet #": "1",
                "Section #": "1010",
                "Title": "Series 10",
                "Description": "Placeholder Row",
                "Overshot OD": "1.5625",
                "Part #": "N/A",
                "Logan Part #": "N/A",
                "Logan Description": "",
                "Size": "",
                "Complete Assembly Number": "9790",
                "Total Length": "",
                "Diameter of Largest Wicker": "",
                "Diameter of Smallest Wicker": "",
                "Catch Size": "",
                "Nominal Size/Nominal Catch Size": "",
                "Assembly dressed to packoff": "",
                "Shoe OD": "",
                "Hole Size": "",
                "Inside Diameter": "",
            },
        ]
    )

    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        sample_data.to_excel(writer, sheet_name="Data", index=False)

    records_df = build_item_records_dataframe(
        workbook_path=workbook_path,
        pricebook_version="Test Pricebook",
    )

    assert len(records_df) == 3

    first_record = records_df.iloc[0]
    assert first_record["part_number"] == "9790"
    assert first_record["part_number_normalized"] == "9790"
    assert first_record["source_sheet"] == "Data"
    assert first_record["source_row_number"] == "2"
    assert first_record["is_valid_candidate"] == "true"
    assert first_record["total_length"] == "10.5"
    assert first_record["diameter_largest_wicker"] == "5.25"
    assert first_record["diameter_smallest_wicker"] == "4.75"
    assert first_record["assembly_dressed_to_packoff"] == "Yes"
    assert "Total Length: 10.5" in first_record["search_text"]
    assert "Diameter of Largest Wicker: 5.25" in first_record["search_text"]
    assert "Diameter of Smallest Wicker: 4.75" in first_record["search_text"]
    assert "Assembly Dressed to Packoff: Yes" in first_record["search_text"]
    assert "Logan Part Number: N/A" not in first_record["search_text"]

    placeholder_record = records_df.iloc[2]
    assert placeholder_record["part_number"] == "N/A"
    assert placeholder_record["is_valid_candidate"] == "false"
    assert placeholder_record["invalid_reason"] == "placeholder_part_number"
