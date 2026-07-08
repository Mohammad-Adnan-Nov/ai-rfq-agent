from __future__ import annotations

import pytest

from rfq_agent.retrieval.assembly_search import (
    build_assembly_number_search_sql,
    map_assembly_number_search_row,
    normalize_assembly_number_query,
)


def test_normalize_assembly_number_query_accepts_plain_number() -> None:
    assert normalize_assembly_number_query("47264") == "47264"


def test_normalize_assembly_number_query_removes_ca_prefix() -> None:
    assert normalize_assembly_number_query("CA# 47264") == "47264"


def test_normalize_assembly_number_query_removes_bowen_ca_prefix() -> None:
    assert normalize_assembly_number_query("Bowen CA# 47264") == "47264"


def test_normalize_assembly_number_query_rejects_blank() -> None:
    with pytest.raises(ValueError, match="cannot be blank"):
        normalize_assembly_number_query("   ")


def test_build_assembly_number_search_sql_excludes_invalid_by_default() -> None:
    sql = build_assembly_number_search_sql(
        include_invalid=False,
        active_only=True,
        limit=25,
    )

    assert "TOP (25)" in sql
    assert "pi.complete_assembly_number IS NOT NULL" in sql
    assert "pi.is_valid_candidate = 1" in sql
    assert "pv.is_active = 1" in sql
    assert "assembly_match_rank" in sql


def test_build_assembly_number_search_sql_can_include_invalid_rows() -> None:
    sql = build_assembly_number_search_sql(
        include_invalid=True,
        active_only=True,
        limit=25,
    )

    assert "pi.complete_assembly_number IS NOT NULL" in sql
    assert "pi.is_valid_candidate = 1" not in sql


def test_map_assembly_number_search_row() -> None:
    row = {
        "pricebook_item_id": 10,
        "part_id": 20,
        "part_number": "ABC 123",
        "part_number_normalized": "ABC123",
        "description": "Test Description",
        "logan_part_number": "L-123",
        "logan_description": "Logan Description",
        "complete_assembly_number": "47264",
        "is_valid_candidate": True,
        "product_family": "Fishing Tools",
        "version_name": "Fishing Tools PB 2022 Jun",
        "section_number": "1000",
        "sheet_number": "10",
        "section_title": "Test Section",
        "source_workbook": "workbook.xlsx",
        "source_sheet": "Data",
        "source_row_number": 123,
        "search_text_preview": "Complete Assembly Number: 47264",
    }

    result = map_assembly_number_search_row(
        row=row,
        matched_assembly_number_normalized="47264",
    )

    assert result.pricebook_item_id == 10
    assert result.part_id == 20
    assert result.part_number == "ABC 123"
    assert result.complete_assembly_number == "47264"
    assert result.matched_assembly_number_normalized == "47264"
    assert result.is_valid_candidate is True
    assert result.source_row_number == 123
