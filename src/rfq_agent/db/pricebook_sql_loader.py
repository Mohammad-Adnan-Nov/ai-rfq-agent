from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from rfq_agent.db.sql_connection import connect_sql_server
from rfq_agent.ingestion.data_sheet_parser import clean_text
from rfq_agent.ingestion.item_quality_report import read_item_records_csv
from rfq_agent.ingestion.item_record_builder import OUTPUT_COLUMNS, is_placeholder_part_number


ATTRIBUTE_NAMES = [
    "overshot_od",
    "size",
    "total_length",
    "diameter_largest_wicker",
    "diameter_smallest_wicker",
    "catch_size",
    "nominal_size_or_catch_size",
    "assembly_dressed_to_packoff",
    "shoe_od",
    "hole_size",
    "inside_diameter",
]

INGESTION_STATUS_COMPLETED = "success"

TARGET_TABLES_REQUIRING_EMPTY_LOAD = [
    "pricebook_versions",
    "pricebook_sections",
    "parts",
    "pricebook_items",
    "item_attributes",
    "item_search_index",
    "ingestion_runs",
]


@dataclass(frozen=True)
class PricebookSqlLoadConfig:
    server: str
    database: str
    input_csv: Path
    source_workbook: Path
    product_family: str
    version_code: str
    version_name: str
    search_text_version: str = "v1"


@dataclass(frozen=True)
class PricebookSqlLoadReport:
    input_csv: str
    source_workbook: str
    source_file_hash: str | None
    product_family: str
    version_code: str
    version_name: str
    csv_row_count: int
    unique_section_count: int
    unique_part_count: int
    pricebook_item_count: int
    valid_candidate_count: int
    invalid_candidate_count: int
    duplicate_valid_part_context_count: int
    attribute_row_count_prepared: int
    search_index_row_count_prepared: int
    dry_run: bool
    status: str
    pricebook_version_id: int | None = None
    ingestion_run_id: int | None = None
    attribute_rows_inserted: int | None = None
    search_rows_inserted: int | None = None


@dataclass(frozen=True)
class PreparedPricebookLoad:
    sections: dict[tuple[str, str, str, str], dict[str, str]]
    parts: dict[str, dict[str, Any]]
    items: list[dict[str, Any]]
    attributes: list[dict[str, Any]]
    search_rows: list[dict[str, Any]]
    valid_candidate_count: int
    invalid_candidate_count: int
    duplicate_valid_part_context_count: int


def none_if_blank(value: Any) -> str | None:
    text = clean_text(value)
    return text if text else None


def truncate(value: str | None, max_length: int) -> str | None:
    if value is None:
        return None
    return value[:max_length]


def normalize_for_sql_key(value: Any) -> str:
    text = clean_text(value).lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def to_bit(value: Any) -> int:
    text = clean_text(value).lower()
    return 1 if text in {"true", "1", "yes", "y"} else 0


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None

    digest = hashlib.sha256()

    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def validate_item_records_dataframe(df: pd.DataFrame) -> None:
    missing_columns = [column for column in OUTPUT_COLUMNS if column not in df.columns]

    if missing_columns:
        raise RuntimeError(
            "Input CSV is not the canonical item-record output. "
            f"Missing columns: {missing_columns}"
        )

    blank_part_rows = int((df["part_number"].map(clean_text) == "").sum())

    if blank_part_rows:
        raise RuntimeError(
            "The SQL schema requires a part_id for every pricebook item. "
            f"Found {blank_part_rows} rows with blank part_number."
        )

    blank_normalized_rows = int((df["part_number_normalized"].map(clean_text) == "").sum())

    if blank_normalized_rows:
        raise RuntimeError(
            "The SQL schema requires normalized part numbers. "
            f"Found {blank_normalized_rows} rows with blank part_number_normalized."
        )


def count_duplicate_valid_part_contexts(df: pd.DataFrame) -> int:
    valid_df = df[df["is_valid_candidate"].map(to_bit) == 1].copy()
    normalized = valid_df["part_number_normalized"].map(clean_text)
    normalized = normalized[normalized != ""]
    return int(normalized.duplicated().sum())


def prepare_pricebook_load(df: pd.DataFrame) -> PreparedPricebookLoad:
    validate_item_records_dataframe(df)

    sections: dict[tuple[str, str, str, str], dict[str, str]] = {}
    parts: dict[str, dict[str, Any]] = {}
    items: list[dict[str, Any]] = []
    attributes: list[dict[str, Any]] = []
    search_rows: list[dict[str, Any]] = []

    for csv_index, row in df.iterrows():
        section_number = truncate(none_if_blank(row["section_number"]), 50) or "UNKNOWN"
        sheet_number = truncate(none_if_blank(row["sheet_number"]), 50) or "UNKNOWN"
        title = truncate(none_if_blank(row["title"]), 255) or "UNKNOWN SECTION TITLE"
        source_sheet = truncate(none_if_blank(row["source_sheet"]), 255) or "Data"

        section_number_normalized = truncate(normalize_for_sql_key(section_number), 50) or "unknown"
        sheet_number_normalized = truncate(normalize_for_sql_key(sheet_number), 50) or "unknown"
        title_normalized = truncate(normalize_for_sql_key(title), 255) or "unknown section title"

        section_key = (
            section_number_normalized,
            sheet_number_normalized,
            title_normalized,
            source_sheet,
        )

        if section_key not in sections:
            sections[section_key] = {
                "section_number": section_number,
                "section_number_normalized": section_number_normalized,
                "sheet_number": sheet_number,
                "sheet_number_normalized": sheet_number_normalized,
                "title": title,
                "title_normalized": title_normalized,
                "source_sheet": source_sheet,
            }

        part_number = truncate(none_if_blank(row["part_number"]), 100)
        part_number_normalized = truncate(none_if_blank(row["part_number_normalized"]), 100)

        if part_number is None or part_number_normalized is None:
            raise RuntimeError(f"Invalid blank part number at CSV row index {csv_index}.")

        invalid_reason = truncate(none_if_blank(row["invalid_reason"]), 100)
        is_placeholder = int(
            invalid_reason == "placeholder_part_number"
            or is_placeholder_part_number(part_number)
        )

        if part_number_normalized not in parts:
            parts[part_number_normalized] = {
                "part_number": part_number,
                "part_number_normalized": part_number_normalized,
                "is_placeholder": is_placeholder,
            }

        source_row_number_text = clean_text(row["source_row_number"])

        if not source_row_number_text.isdigit():
            raise RuntimeError(
                f"Invalid source_row_number at CSV row index {csv_index}: "
                f"{source_row_number_text!r}"
            )

        is_valid_candidate = to_bit(row["is_valid_candidate"])

        items.append(
            {
                "csv_index": int(csv_index), #type: ignore
                "section_key": section_key,
                "part_number_normalized": part_number_normalized,
                "description": truncate(none_if_blank(row["description"]), 1000),
                "logan_part_number": truncate(none_if_blank(row["logan_part_number"]), 100),
                "logan_description": truncate(none_if_blank(row["logan_description"]), 1000),
                "complete_assembly_number": truncate(
                    none_if_blank(row["complete_assembly_number"]),
                    100,
                ),
                "is_valid_candidate": is_valid_candidate,
                "invalid_reason": invalid_reason,
                "source_workbook": truncate(none_if_blank(row["source_workbook"]), 255),
                "source_sheet": source_sheet,
                "source_row_number": int(source_row_number_text),
            }
        )

        for attribute_name in ATTRIBUTE_NAMES:
            attribute_value = none_if_blank(row[attribute_name])
            if attribute_value is None:
                continue

            attributes.append(
                {
                    "csv_index": int(csv_index), #type: ignore
                    "attribute_name": attribute_name,
                    "attribute_value_text": truncate(attribute_value, 500),
                    "attribute_value_normalized": truncate(
                        normalize_for_sql_key(attribute_value),
                        500,
                    ),
                }
            )

        search_text = none_if_blank(row["search_text"])

        if is_valid_candidate and search_text:
            search_rows.append(
                {
                    "csv_index": int(csv_index), #type: ignore
                    "search_text": search_text,
                }
            )

    valid_candidate_count = int((df["is_valid_candidate"].map(to_bit) == 1).sum())
    invalid_candidate_count = int(len(df) - valid_candidate_count)

    return PreparedPricebookLoad(
        sections=sections,
        parts=parts,
        items=items,
        attributes=attributes,
        search_rows=search_rows,
        valid_candidate_count=valid_candidate_count,
        invalid_candidate_count=invalid_candidate_count,
        duplicate_valid_part_context_count=count_duplicate_valid_part_contexts(df),
    )


def build_report(
    config: PricebookSqlLoadConfig,
    prepared: PreparedPricebookLoad,
    source_file_hash: str | None,
    dry_run: bool,
    status: str,
    pricebook_version_id: int | None = None,
    ingestion_run_id: int | None = None,
    attribute_rows_inserted: int | None = None,
    search_rows_inserted: int | None = None,
) -> PricebookSqlLoadReport:
    return PricebookSqlLoadReport(
        input_csv=str(config.input_csv),
        source_workbook=str(config.source_workbook),
        source_file_hash=source_file_hash,
        product_family=config.product_family,
        version_code=config.version_code,
        version_name=config.version_name,
        csv_row_count=len(prepared.items),
        unique_section_count=len(prepared.sections),
        unique_part_count=len(prepared.parts),
        pricebook_item_count=len(prepared.items),
        valid_candidate_count=prepared.valid_candidate_count,
        invalid_candidate_count=prepared.invalid_candidate_count,
        duplicate_valid_part_context_count=prepared.duplicate_valid_part_context_count,
        attribute_row_count_prepared=len(prepared.attributes),
        search_index_row_count_prepared=len(prepared.search_rows),
        dry_run=dry_run,
        status=status,
        pricebook_version_id=pricebook_version_id,
        ingestion_run_id=ingestion_run_id,
        attribute_rows_inserted=attribute_rows_inserted,
        search_rows_inserted=search_rows_inserted,
    )


def write_report(report: PricebookSqlLoadReport, output_path: str | Path) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def require_empty_target(cursor: Any) -> None:
    non_empty: list[tuple[str, int]] = []

    for table in TARGET_TABLES_REQUIRING_EMPTY_LOAD:
        cursor.execute(f"SELECT COUNT(*) FROM rfq.{table};")
        count = int(cursor.fetchone()[0])

        if count:
            non_empty.append((table, count))

    if non_empty:
        details = ", ".join(f"{table}={count}" for table, count in non_empty)
        raise RuntimeError(
            "Target tables are not empty. Refusing to load to avoid duplicate "
            f"or partial data. Non-empty tables: {details}"
        )


def insert_pricebook_version(
    cursor: Any,
    config: PricebookSqlLoadConfig,
    source_file_hash: str | None,
) -> int:
    cursor.execute(
        """
        INSERT INTO rfq.pricebook_versions (
            product_family,
            version_code,
            version_name,
            source_workbook_name,
            source_file_hash,
            is_active,
            created_at
        )
        OUTPUT INSERTED.pricebook_version_id
        VALUES (?, ?, ?, ?, ?, 1, SYSUTCDATETIME());
        """,
        config.product_family,
        config.version_code,
        config.version_name,
        config.source_workbook.name,
        source_file_hash,
    )

    return int(cursor.fetchone()[0])


def insert_sections(
    cursor: Any,
    pricebook_version_id: int,
    sections: dict[tuple[str, str, str, str], dict[str, str]],
) -> dict[tuple[str, str, str, str], int]:
    section_id_by_key: dict[tuple[str, str, str, str], int] = {}

    for section_key, section in sections.items():
        cursor.execute(
            """
            INSERT INTO rfq.pricebook_sections (
                pricebook_version_id,
                section_number,
                section_number_normalized,
                sheet_number,
                sheet_number_normalized,
                title,
                title_normalized,
                source_sheet,
                created_at
            )
            OUTPUT INSERTED.section_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME());
            """,
            pricebook_version_id,
            section["section_number"],
            section["section_number_normalized"],
            section["sheet_number"],
            section["sheet_number_normalized"],
            section["title"],
            section["title_normalized"],
            section["source_sheet"],
        )

        section_id_by_key[section_key] = int(cursor.fetchone()[0])

    return section_id_by_key


def insert_parts(
    cursor: Any,
    parts: dict[str, dict[str, Any]],
) -> dict[str, int]:
    part_id_by_normalized: dict[str, int] = {}

    for part_number_normalized, part in parts.items():
        cursor.execute(
            """
            INSERT INTO rfq.parts (
                part_number,
                part_number_normalized,
                is_placeholder,
                created_at
            )
            OUTPUT INSERTED.part_id
            VALUES (?, ?, ?, SYSUTCDATETIME());
            """,
            part["part_number"],
            part["part_number_normalized"],
            part["is_placeholder"],
        )

        part_id_by_normalized[part_number_normalized] = int(cursor.fetchone()[0])

    return part_id_by_normalized


def insert_items(
    cursor: Any,
    pricebook_version_id: int,
    items: list[dict[str, Any]],
    section_id_by_key: dict[tuple[str, str, str, str], int],
    part_id_by_normalized: dict[str, int],
) -> dict[int, int]:
    item_id_by_csv_index: dict[int, int] = {}

    for item in items:
        cursor.execute(
            """
            INSERT INTO rfq.pricebook_items (
                pricebook_version_id,
                section_id,
                part_id,
                description,
                logan_part_number,
                logan_description,
                complete_assembly_number,
                is_valid_candidate,
                invalid_reason,
                source_workbook,
                source_sheet,
                source_row_number,
                created_at
            )
            OUTPUT INSERTED.pricebook_item_id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, SYSUTCDATETIME());
            """,
            pricebook_version_id,
            section_id_by_key[item["section_key"]],
            part_id_by_normalized[item["part_number_normalized"]],
            item["description"],
            item["logan_part_number"],
            item["logan_description"],
            item["complete_assembly_number"],
            item["is_valid_candidate"],
            item["invalid_reason"],
            item["source_workbook"],
            item["source_sheet"],
            item["source_row_number"],
        )

        item_id_by_csv_index[item["csv_index"]] = int(cursor.fetchone()[0])

    return item_id_by_csv_index


def get_attribute_definition_ids(cursor: Any) -> dict[str, int]:
    cursor.execute(
        """
        SELECT attribute_name, attribute_definition_id
        FROM rfq.attribute_definitions;
        """
    )

    return {str(row[0]): int(row[1]) for row in cursor.fetchall()}


def insert_attributes(
    cursor: Any,
    attributes: list[dict[str, Any]],
    item_id_by_csv_index: dict[int, int],
    attribute_definition_ids: dict[str, int],
) -> int:
    inserted = 0

    for attribute in attributes:
        attribute_name = attribute["attribute_name"]

        if attribute_name not in attribute_definition_ids:
            raise RuntimeError(f"Missing seeded attribute definition: {attribute_name}")

        cursor.execute(
            """
            INSERT INTO rfq.item_attributes (
                pricebook_item_id,
                attribute_definition_id,
                attribute_value_text,
                attribute_value_normalized,
                created_at
            )
            VALUES (?, ?, ?, ?, SYSUTCDATETIME());
            """,
            item_id_by_csv_index[attribute["csv_index"]],
            attribute_definition_ids[attribute_name],
            attribute["attribute_value_text"],
            attribute["attribute_value_normalized"],
        )

        inserted += 1

    return inserted


def insert_search_rows(
    cursor: Any,
    search_rows: list[dict[str, Any]],
    item_id_by_csv_index: dict[int, int],
    search_text_version: str,
) -> int:
    inserted = 0

    for search_row in search_rows:
        cursor.execute(
            """
            INSERT INTO rfq.item_search_index (
                pricebook_item_id,
                search_text,
                search_text_version,
                created_at
            )
            VALUES (?, ?, ?, SYSUTCDATETIME());
            """,
            item_id_by_csv_index[search_row["csv_index"]],
            search_row["search_text"],
            search_text_version,
        )

        inserted += 1

    return inserted


def insert_ingestion_run(
    cursor: Any,
    pricebook_version_id: int,
    config: PricebookSqlLoadConfig,
    source_file_hash: str | None,
    prepared: PreparedPricebookLoad,
) -> int:
    cursor.execute(
        """
        INSERT INTO rfq.ingestion_runs (
            pricebook_version_id,
            source_workbook_name,
            source_file_hash,
            input_row_count,
            output_row_count,
            valid_candidate_count,
            invalid_candidate_count,
            duplicate_context_count,
            status,
            error_message,
            started_at,
            finished_at
        )
        OUTPUT INSERTED.ingestion_run_id
        VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, SYSUTCDATETIME(), SYSUTCDATETIME()
        );
        """,
        pricebook_version_id,
        config.source_workbook.name,
        source_file_hash,
        len(prepared.items),
        len(prepared.items),
        prepared.valid_candidate_count,
        prepared.invalid_candidate_count,
        prepared.duplicate_valid_part_context_count,
        INGESTION_STATUS_COMPLETED,
    )

    return int(cursor.fetchone()[0])


def load_pricebook_to_sql(
    config: PricebookSqlLoadConfig,
    dry_run: bool,
) -> PricebookSqlLoadReport:
    df = read_item_records_csv(config.input_csv)
    prepared = prepare_pricebook_load(df)
    source_file_hash = sha256_file(config.source_workbook)

    if dry_run:
        return build_report(
            config=config,
            prepared=prepared,
            source_file_hash=source_file_hash,
            dry_run=True,
            status="dry_run_completed",
        )

    connection = connect_sql_server(server=config.server, database=config.database)

    try:
        cursor = connection.cursor()
        require_empty_target(cursor)

        pricebook_version_id = insert_pricebook_version(cursor, config, source_file_hash)

        section_id_by_key = insert_sections(
            cursor=cursor,
            pricebook_version_id=pricebook_version_id,
            sections=prepared.sections,
        )

        part_id_by_normalized = insert_parts(
            cursor=cursor,
            parts=prepared.parts,
        )

        item_id_by_csv_index = insert_items(
            cursor=cursor,
            pricebook_version_id=pricebook_version_id,
            items=prepared.items,
            section_id_by_key=section_id_by_key,
            part_id_by_normalized=part_id_by_normalized,
        )

        attribute_definition_ids = get_attribute_definition_ids(cursor)

        attribute_rows_inserted = insert_attributes(
            cursor=cursor,
            attributes=prepared.attributes,
            item_id_by_csv_index=item_id_by_csv_index,
            attribute_definition_ids=attribute_definition_ids,
        )

        search_rows_inserted = insert_search_rows(
            cursor=cursor,
            search_rows=prepared.search_rows,
            item_id_by_csv_index=item_id_by_csv_index,
            search_text_version=config.search_text_version,
        )

        ingestion_run_id = insert_ingestion_run(
            cursor=cursor,
            pricebook_version_id=pricebook_version_id,
            config=config,
            source_file_hash=source_file_hash,
            prepared=prepared,
        )

        connection.commit()

        return build_report(
            config=config,
            prepared=prepared,
            source_file_hash=source_file_hash,
            dry_run=False,
            status="success",
            pricebook_version_id=pricebook_version_id,
            ingestion_run_id=ingestion_run_id,
            attribute_rows_inserted=attribute_rows_inserted,
            search_rows_inserted=search_rows_inserted,
        )

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
