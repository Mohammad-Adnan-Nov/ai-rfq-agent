from __future__ import annotations

import pytest

from rfq_agent.retrieval.exact_search import (
    build_exact_part_search_sql,
    map_exact_part_search_row,
    normalize_exact_part_query,
    validate_limit,
)


def test_normalize_exact_part_query_removes_spaces_and_uppercases() -> None:
    assert normalize_exact_part_query(" abc 123 ") == "ABC123"


def test_normalize_exact_part_query_rejects_blank_value() -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        normalize_exact_part_query("   ")


def test_validate_limit_rejects_zero() -> None:
    with pytest.raises(ValueError, match="greater than or equal to 1"):
        validate_limit(0)


def test_validate_limit_rejects_too_large_value() -> None:
    with pytest.raises(ValueError, match="less than or equal to 500"):
        validate_limit(501)


def test_build_exact_part_search_sql_excludes_invalid_by_default() -> None:
    sql = build_exact_part_search_sql(
        include_invalid=False,
        active_only=True,
        limit=25,
    )

    assert "TOP (25)" in sql
    assert "p.part_number_normalized = ?" in sql
    assert "pi.is_valid_candidate = 1" in sql
    assert "pv.is_active = 1" in sql


def test_build_exact_part_search_sql_can_include_invalid_rows() -> None:
    sql = build_exact_part_search_sql(
        include_invalid=True,
        active_only=True,
        limit=25,
    )

    assert "p.part_number_normalized = ?" in sql
    assert "pi.is_valid_candidate = 1" not in sql


def test_map_exact_part_search_row() -> None:
    row = {
        "pricebook_item_id": 10,
        "part_id": 20,
        "part_number": "ABC 123",
        "part_number_normalized": "ABC123",
        "description": "Test Description",
        "logan_part_number": "L-123",
        "logan_description": "Logan Description",
        "complete_assembly_number": "CA-999",
        "is_valid_candidate": True,
        "product_family": "Fishing Tools",
        "version_name": "Fishing Tools PB 2022 Jun",
        "section_number": "1000",
        "sheet_number": "10",
        "section_title": "Test Section",
        "source_workbook": "workbook.xlsx",
        "source_sheet": "Data",
        "source_row_number": 123,
        "search_text_preview": "Part Number: ABC 123",
    }

    result = map_exact_part_search_row(row)

    assert result.pricebook_item_id == 10
    assert result.part_id == 20
    assert result.part_number == "ABC 123"
    assert result.part_number_normalized == "ABC123"
    assert result.is_valid_candidate is True
    assert result.source_row_number == 123
