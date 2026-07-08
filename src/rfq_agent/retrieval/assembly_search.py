from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from rfq_agent.ingestion.data_sheet_parser import clean_text
from rfq_agent.retrieval.exact_search import row_to_dicts, validate_limit


@dataclass(frozen=True)
class AssemblyNumberSearchResult:
    pricebook_item_id: int
    part_id: int
    part_number: str
    part_number_normalized: str
    description: str | None
    logan_part_number: str | None
    logan_description: str | None
    complete_assembly_number: str | None
    matched_assembly_number_normalized: str
    is_valid_candidate: bool
    product_family: str
    version_name: str
    section_number: str | None
    sheet_number: str | None
    section_title: str | None
    source_workbook: str
    source_sheet: str
    source_row_number: int
    search_text_preview: str | None


def normalize_assembly_number_query(value: Any) -> str:
    """
    Normalize assembly-number user input.

    Examples:
    - "47264" -> "47264"
    - "CA# 47264" -> "47264"
    - "Bowen CA# 47264" -> "47264"

    This is intentionally conservative. It supports retrieval, but it does not
    claim that an assembly/component relationship is verified BOM truth.
    """
    text = clean_text(value).upper()

    if not text:
        raise ValueError("Assembly number query cannot be blank.")

    text = text.replace("COMPLETE ASSEMBLY NUMBER", "")
    text = text.replace("ASSEMBLY NUMBER", "")
    text = text.replace("BOWEN", "")
    text = text.replace("CA#", "CA")

    normalized = re.sub(r"[^A-Z0-9]", "", text)

    if normalized.startswith("CA") and len(normalized) > 2:
        remainder = normalized[2:]
        if any(character.isdigit() for character in remainder):
            normalized = remainder

    if not normalized:
        raise ValueError("Assembly number query cannot be blank after normalization.")

    return normalized


def sql_normalized_complete_assembly_expression() -> str:
    return """
        UPPER(
            REPLACE(
                REPLACE(
                    REPLACE(
                        REPLACE(
                            REPLACE(
                                REPLACE(
                                    LTRIM(RTRIM(pi.complete_assembly_number)),
                                    ' ',
                                    ''
                                ),
                                '#',
                                ''
                            ),
                            '-',
                            ''
                        ),
                        '/',
                        ''
                    ),
                    '.',
                    ''
                ),
                CHAR(9),
                ''
            )
        )
    """


def build_assembly_number_search_sql(
    *,
    include_invalid: bool,
    active_only: bool,
    limit: int,
) -> str:
    safe_limit = validate_limit(limit)
    assembly_expr = sql_normalized_complete_assembly_expression()

    filters = [
        "pi.complete_assembly_number IS NOT NULL",
        "LTRIM(RTRIM(pi.complete_assembly_number)) <> ''",
        f"""
        (
            {assembly_expr} = ?
            OR {assembly_expr} = 'CA' + ?
            OR (
                LEN(?) >= 4
                AND {assembly_expr} LIKE '%' + ? + '%'
            )
        )
        """,
    ]

    if not include_invalid:
        filters.append("pi.is_valid_candidate = 1")

    if active_only:
        filters.append("pv.is_active = 1")

    where_clause = "\n          AND ".join(filters)

    return f"""
        SELECT TOP ({safe_limit})
            pi.pricebook_item_id,
            p.part_id,
            p.part_number,
            p.part_number_normalized,
            pi.description,
            pi.logan_part_number,
            pi.logan_description,
            pi.complete_assembly_number,
            pi.is_valid_candidate,
            pv.product_family,
            pv.version_name,
            ps.section_number,
            ps.sheet_number,
            ps.title AS section_title,
            pi.source_workbook,
            pi.source_sheet,
            pi.source_row_number,
            LEFT(si.search_text, 500) AS search_text_preview,
            CASE
                WHEN {assembly_expr} = ? THEN 0
                WHEN {assembly_expr} = 'CA' + ? THEN 1
                ELSE 2
            END AS assembly_match_rank
        FROM rfq.pricebook_items pi
        JOIN rfq.parts p
            ON p.part_id = pi.part_id
        JOIN rfq.pricebook_versions pv
            ON pv.pricebook_version_id = pi.pricebook_version_id
        LEFT JOIN rfq.pricebook_sections ps
            ON ps.section_id = pi.section_id
        LEFT JOIN rfq.item_search_index si
            ON si.pricebook_item_id = pi.pricebook_item_id
        WHERE {where_clause}
        ORDER BY
            assembly_match_rank ASC,
            pi.is_valid_candidate DESC,
            pv.created_at DESC,
            pi.pricebook_item_id ASC;
    """


def map_assembly_number_search_row(
    row: dict[str, Any],
    matched_assembly_number_normalized: str,
) -> AssemblyNumberSearchResult:
    return AssemblyNumberSearchResult(
        pricebook_item_id=int(row["pricebook_item_id"]),
        part_id=int(row["part_id"]),
        part_number=str(row["part_number"]),
        part_number_normalized=str(row["part_number_normalized"]),
        description=row.get("description"),
        logan_part_number=row.get("logan_part_number"),
        logan_description=row.get("logan_description"),
        complete_assembly_number=row.get("complete_assembly_number"),
        matched_assembly_number_normalized=matched_assembly_number_normalized,
        is_valid_candidate=bool(row["is_valid_candidate"]),
        product_family=str(row["product_family"]),
        version_name=str(row["version_name"]),
        section_number=row.get("section_number"),
        sheet_number=row.get("sheet_number"),
        section_title=row.get("section_title"),
        source_workbook=str(row["source_workbook"]),
        source_sheet=str(row["source_sheet"]),
        source_row_number=int(row["source_row_number"]),
        search_text_preview=row.get("search_text_preview"),
    )


def search_complete_assembly_number(
    connection: Any,
    assembly_number: str,
    *,
    include_invalid: bool = False,
    active_only: bool = True,
    limit: int = 50,
) -> list[AssemblyNumberSearchResult]:
    normalized_query = normalize_assembly_number_query(assembly_number)

    sql = build_assembly_number_search_sql(
        include_invalid=include_invalid,
        active_only=active_only,
        limit=limit,
    )

    cursor = connection.cursor()
    cursor.execute(
        sql,
        normalized_query,
        normalized_query,
        normalized_query,
        normalized_query,
        normalized_query,
        normalized_query,
    )

    rows = row_to_dicts(cursor)

    return [
        map_assembly_number_search_row(
            row=row,
            matched_assembly_number_normalized=normalized_query,
        )
        for row in rows
    ]


def assembly_number_results_to_dicts(
    results: list[AssemblyNumberSearchResult],
) -> list[dict[str, Any]]:
    return [asdict(result) for result in results]
