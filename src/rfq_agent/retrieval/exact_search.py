from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from rfq_agent.ingestion.item_record_builder import normalize_part_number


@dataclass(frozen=True)
class ExactPartSearchResult:
    pricebook_item_id: int
    part_id: int
    part_number: str
    part_number_normalized: str
    description: str | None
    logan_part_number: str | None
    logan_description: str | None
    complete_assembly_number: str | None
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


def normalize_exact_part_query(part_number: str) -> str:
    normalized = normalize_part_number(part_number)

    if not normalized:
        raise ValueError("Part number query cannot be blank.")

    return normalized


def validate_limit(limit: int) -> int:
    if limit < 1:
        raise ValueError("limit must be greater than or equal to 1.")

    if limit > 500:
        raise ValueError("limit must be less than or equal to 500.")

    return limit


def build_exact_part_search_sql(
    *,
    include_invalid: bool,
    active_only: bool,
    limit: int,
) -> str:
    safe_limit = validate_limit(limit)

    filters = ["p.part_number_normalized = ?"]

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
            LEFT(si.search_text, 500) AS search_text_preview
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
            pi.is_valid_candidate DESC,
            pv.created_at DESC,
            pi.pricebook_item_id ASC;
    """


def row_to_dicts(cursor: Any) -> list[dict[str, Any]]:
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]


def map_exact_part_search_row(row: dict[str, Any]) -> ExactPartSearchResult:
    return ExactPartSearchResult(
        pricebook_item_id=int(row["pricebook_item_id"]),
        part_id=int(row["part_id"]),
        part_number=str(row["part_number"]),
        part_number_normalized=str(row["part_number_normalized"]),
        description=row.get("description"),
        logan_part_number=row.get("logan_part_number"),
        logan_description=row.get("logan_description"),
        complete_assembly_number=row.get("complete_assembly_number"),
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


def search_exact_part_number(
    connection: Any,
    part_number: str,
    *,
    include_invalid: bool = False,
    active_only: bool = True,
    limit: int = 50,
) -> list[ExactPartSearchResult]:
    normalized_query = normalize_exact_part_query(part_number)

    sql = build_exact_part_search_sql(
        include_invalid=include_invalid,
        active_only=active_only,
        limit=limit,
    )

    cursor = connection.cursor()
    cursor.execute(sql, normalized_query)

    rows = row_to_dicts(cursor)

    return [map_exact_part_search_row(row) for row in rows]


def exact_part_results_to_dicts(
    results: list[ExactPartSearchResult],
) -> list[dict[str, Any]]:
    return [asdict(result) for result in results]
