from pathlib import Path

from rfq_agent.db.sql_static_review import run_static_sql_review


def test_static_sql_review_passes_for_minimal_expected_sql(tmp_path: Path):
    sql_path = tmp_path / "ddl.sql"

    sql_path.write_text(
        """
        CREATE SCHEMA rfq;

        CREATE TABLE rfq.pricebook_versions (
            product_family NVARCHAR(100) NOT NULL,
            source_file_hash NVARCHAR(128) NULL
        );

        CREATE TABLE rfq.pricebook_sections (
            section_number_normalized NVARCHAR(50) NOT NULL,
            sheet_number_normalized NVARCHAR(50) NOT NULL,
            title_normalized NVARCHAR(255) NOT NULL
        );

        CREATE TABLE rfq.parts (
            part_number NVARCHAR(100) NOT NULL,
            part_number_normalized NVARCHAR(100) NOT NULL
        );

        CREATE TABLE rfq.pricebook_items (
            CONSTRAINT UQ_pricebook_items_source_row UNIQUE (source_row_number)
        );

        CREATE TABLE rfq.attribute_definitions (
            attribute_name NVARCHAR(100) NOT NULL
        );

        CREATE TABLE rfq.item_attributes (
            CONSTRAINT UQ_item_attributes_item_attribute
                UNIQUE (pricebook_item_id, attribute_definition_id)
        );

        CREATE TABLE rfq.item_search_index (
            CONSTRAINT UQ_item_search_index_pricebook_item UNIQUE (pricebook_item_id)
        );

        CREATE TABLE rfq.ingestion_runs (
            CONSTRAINT CK_ingestion_runs_status
                CHECK (status IN ('started', 'success', 'failed'))
        );

        CREATE TABLE rfq.relationship_type_definitions (
            relationship_type_code NVARCHAR(100) NOT NULL
        );

        CREATE TABLE rfq.part_relationships (
            relationship_type_code NVARCHAR(100) NOT NULL,
            CONSTRAINT FK_part_relationships_relationship_types
                FOREIGN KEY (relationship_type_code)
                REFERENCES rfq.relationship_type_definitions(relationship_type_code),
            CONSTRAINT CK_part_relationships_confidence_level
                CHECK (confidence_level IN ('derived', 'verified', 'manual')),
            CONSTRAINT CK_part_relationships_no_self_reference
                CHECK (parent_part_id <> child_part_id),
            CONSTRAINT CK_part_relationships_no_same_pricebook_item
                CHECK (
                    parent_pricebook_item_id IS NULL
                    OR child_pricebook_item_id IS NULL
                    OR parent_pricebook_item_id <> child_pricebook_item_id
                )
        );

        CREATE TABLE rfq.domain_synonyms (
            term_normalized NVARCHAR(100) NOT NULL,
            canonical_term_normalized NVARCHAR(100) NOT NULL,
            scope_key NVARCHAR(100) NOT NULL
        );

        CREATE TABLE rfq.item_aliases (
            alias_text_normalized NVARCHAR(255) NOT NULL,
            CONSTRAINT CK_item_aliases_has_target
                CHECK (part_id IS NOT NULL OR pricebook_item_id IS NOT NULL)
        );

        CREATE UNIQUE INDEX UX_pricebook_versions_one_active_per_family
        ON rfq.pricebook_versions(product_family);

        CREATE UNIQUE INDEX UX_domain_synonyms_active_term_scope
        ON rfq.domain_synonyms(term_normalized, canonical_term_normalized, scope_key);

        CREATE UNIQUE INDEX UX_item_aliases_part_alias_normalized
        ON rfq.item_aliases(part_id, alias_text_normalized);

        CREATE UNIQUE INDEX UX_item_aliases_pricebook_item_alias_normalized
        ON rfq.item_aliases(pricebook_item_id, alias_text_normalized);

        INSERT INTO rfq.attribute_definitions (attribute_name)
        VALUES
            ('overshot_od'),
            ('size'),
            ('total_length'),
            ('diameter_largest_wicker'),
            ('diameter_smallest_wicker'),
            ('catch_size'),
            ('nominal_size_or_catch_size'),
            ('assembly_dressed_to_packoff'),
            ('shoe_od'),
            ('hole_size'),
            ('inside_diameter');

        INSERT INTO rfq.relationship_type_definitions (relationship_type_code)
        VALUES
            ('assembly_contains_component'),
            ('cross_reference'),
            ('alternate_part');
        """,
        encoding="utf-8",
    )

    report = run_static_sql_review(sql_path)

    assert report.passed
    assert report.failed_checks == 0


def test_static_sql_review_fails_when_required_pattern_is_missing(tmp_path: Path):
    sql_path = tmp_path / "ddl.sql"
    sql_path.write_text("CREATE TABLE dbo.parts (part_number INT);", encoding="utf-8")

    report = run_static_sql_review(sql_path)

    assert not report.passed
    assert report.failed_checks > 0
