/*
AI RFQ Agent - Pricebook Foundation Tables
Phase 1 SQL DDL Draft - Production-Oriented V1

Purpose:
Create SQL Server tables for approved Fishing Tool pricebook data.


Execution target order:
1. Local SQL Server / LocalDB / SQL Server Developer Edition
2. Development SQL Server database
3. Test or staging database
4. Production only after review and approval
*/

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

IF NOT EXISTS (
    SELECT 1
    FROM sys.schemas
    WHERE name = 'rfq'
)
BEGIN
    EXEC('CREATE SCHEMA rfq');
END;
GO

CREATE TABLE rfq.pricebook_versions (
    pricebook_version_id BIGINT IDENTITY(1,1) NOT NULL,
    product_family NVARCHAR(100) NOT NULL,
    version_code NVARCHAR(100) NOT NULL,
    version_name NVARCHAR(255) NOT NULL,
    source_workbook_name NVARCHAR(255) NOT NULL,
    source_file_hash NVARCHAR(128) NULL,
    is_active BIT NOT NULL CONSTRAINT DF_pricebook_versions_is_active DEFAULT (1),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_pricebook_versions_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_pricebook_versions PRIMARY KEY (pricebook_version_id),
    CONSTRAINT UQ_pricebook_versions_version_code UNIQUE (version_code)
);
GO

CREATE TABLE rfq.pricebook_sections (
    section_id BIGINT IDENTITY(1,1) NOT NULL,
    pricebook_version_id BIGINT NOT NULL,
    section_number NVARCHAR(50) NOT NULL,
    section_number_normalized NVARCHAR(50) NOT NULL,
    sheet_number NVARCHAR(50) NOT NULL,
    sheet_number_normalized NVARCHAR(50) NOT NULL,
    title NVARCHAR(255) NOT NULL,
    title_normalized NVARCHAR(255) NOT NULL,
    source_sheet NVARCHAR(255) NOT NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_pricebook_sections_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_pricebook_sections PRIMARY KEY (section_id),
    CONSTRAINT FK_pricebook_sections_pricebook_versions
        FOREIGN KEY (pricebook_version_id)
        REFERENCES rfq.pricebook_versions(pricebook_version_id),
    CONSTRAINT UQ_pricebook_sections_context
        UNIQUE (
            pricebook_version_id,
            section_number_normalized,
            sheet_number_normalized,
            title_normalized,
            source_sheet
        )
);
GO

CREATE TABLE rfq.parts (
    part_id BIGINT IDENTITY(1,1) NOT NULL,
    part_number NVARCHAR(100) NOT NULL,
    part_number_normalized NVARCHAR(100) NOT NULL,
    is_placeholder BIT NOT NULL CONSTRAINT DF_parts_is_placeholder DEFAULT (0),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_parts_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_parts PRIMARY KEY (part_id),
    CONSTRAINT UQ_parts_part_number_normalized UNIQUE (part_number_normalized)
);
GO

CREATE TABLE rfq.pricebook_items (
    pricebook_item_id BIGINT IDENTITY(1,1) NOT NULL,
    pricebook_version_id BIGINT NOT NULL,
    section_id BIGINT NULL,
    part_id BIGINT NOT NULL,
    description NVARCHAR(1000) NULL,
    logan_part_number NVARCHAR(100) NULL,
    logan_description NVARCHAR(1000) NULL,
    complete_assembly_number NVARCHAR(100) NULL,
    is_valid_candidate BIT NOT NULL CONSTRAINT DF_pricebook_items_is_valid_candidate DEFAULT (1),
    invalid_reason NVARCHAR(100) NULL,
    source_workbook NVARCHAR(255) NOT NULL,
    source_sheet NVARCHAR(255) NOT NULL,
    source_row_number INT NOT NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_pricebook_items_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_pricebook_items PRIMARY KEY (pricebook_item_id),
    CONSTRAINT FK_pricebook_items_pricebook_versions
        FOREIGN KEY (pricebook_version_id)
        REFERENCES rfq.pricebook_versions(pricebook_version_id),
    CONSTRAINT FK_pricebook_items_pricebook_sections
        FOREIGN KEY (section_id)
        REFERENCES rfq.pricebook_sections(section_id),
    CONSTRAINT FK_pricebook_items_parts
        FOREIGN KEY (part_id)
        REFERENCES rfq.parts(part_id),
    CONSTRAINT UQ_pricebook_items_source_row
        UNIQUE (
            pricebook_version_id,
            source_workbook,
            source_sheet,
            source_row_number
        )
);
GO

CREATE TABLE rfq.attribute_definitions (
    attribute_definition_id BIGINT IDENTITY(1,1) NOT NULL,
    attribute_name NVARCHAR(100) NOT NULL,
    display_name NVARCHAR(255) NOT NULL,
    unit_hint NVARCHAR(50) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_attribute_definitions_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_attribute_definitions PRIMARY KEY (attribute_definition_id),
    CONSTRAINT UQ_attribute_definitions_attribute_name UNIQUE (attribute_name)
);
GO

CREATE TABLE rfq.item_attributes (
    item_attribute_id BIGINT IDENTITY(1,1) NOT NULL,
    pricebook_item_id BIGINT NOT NULL,
    attribute_definition_id BIGINT NOT NULL,
    attribute_value_text NVARCHAR(500) NOT NULL,
    attribute_value_normalized NVARCHAR(500) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_item_attributes_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_item_attributes PRIMARY KEY (item_attribute_id),
    CONSTRAINT FK_item_attributes_pricebook_items
        FOREIGN KEY (pricebook_item_id)
        REFERENCES rfq.pricebook_items(pricebook_item_id),
    CONSTRAINT FK_item_attributes_attribute_definitions
        FOREIGN KEY (attribute_definition_id)
        REFERENCES rfq.attribute_definitions(attribute_definition_id),
    CONSTRAINT UQ_item_attributes_item_attribute
        UNIQUE (pricebook_item_id, attribute_definition_id)
);
GO

CREATE TABLE rfq.item_search_index (
    item_search_index_id BIGINT IDENTITY(1,1) NOT NULL,
    pricebook_item_id BIGINT NOT NULL,
    search_text NVARCHAR(MAX) NOT NULL,
    search_text_version NVARCHAR(50) NOT NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_item_search_index_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_item_search_index PRIMARY KEY (item_search_index_id),
    CONSTRAINT FK_item_search_index_pricebook_items
        FOREIGN KEY (pricebook_item_id)
        REFERENCES rfq.pricebook_items(pricebook_item_id),
    CONSTRAINT UQ_item_search_index_pricebook_item UNIQUE (pricebook_item_id)
);
GO

CREATE TABLE rfq.ingestion_runs (
    ingestion_run_id BIGINT IDENTITY(1,1) NOT NULL,
    pricebook_version_id BIGINT NULL,
    source_workbook_name NVARCHAR(255) NOT NULL,
    source_file_hash NVARCHAR(128) NULL,
    input_row_count INT NOT NULL,
    output_row_count INT NOT NULL,
    valid_candidate_count INT NOT NULL,
    invalid_candidate_count INT NOT NULL,
    duplicate_context_count INT NOT NULL,
    status NVARCHAR(50) NOT NULL,
    error_message NVARCHAR(MAX) NULL,
    started_at DATETIME2 NOT NULL CONSTRAINT DF_ingestion_runs_started_at DEFAULT SYSUTCDATETIME(),
    finished_at DATETIME2 NULL,

    CONSTRAINT PK_ingestion_runs PRIMARY KEY (ingestion_run_id),
    CONSTRAINT FK_ingestion_runs_pricebook_versions
        FOREIGN KEY (pricebook_version_id)
        REFERENCES rfq.pricebook_versions(pricebook_version_id),
    CONSTRAINT CK_ingestion_runs_status
        CHECK (status IN ('started', 'success', 'failed'))
);
GO

CREATE TABLE rfq.relationship_type_definitions (
    relationship_type_code NVARCHAR(100) NOT NULL,
    display_name NVARCHAR(255) NOT NULL,
    description NVARCHAR(1000) NULL,
    is_active BIT NOT NULL CONSTRAINT DF_relationship_type_definitions_is_active DEFAULT (1),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_relationship_type_definitions_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_relationship_type_definitions PRIMARY KEY (relationship_type_code)
);
GO

CREATE TABLE rfq.part_relationships (
    relationship_id BIGINT IDENTITY(1,1) NOT NULL,
    pricebook_version_id BIGINT NOT NULL,
    parent_part_id BIGINT NOT NULL,
    child_part_id BIGINT NOT NULL,
    parent_pricebook_item_id BIGINT NULL,
    child_pricebook_item_id BIGINT NULL,
    relationship_type_code NVARCHAR(100) NOT NULL,
    relationship_source NVARCHAR(100) NOT NULL,
    source_sheet NVARCHAR(255) NULL,
    source_row_number INT NULL,
    confidence_level NVARCHAR(50) NOT NULL CONSTRAINT DF_part_relationships_confidence_level DEFAULT ('derived'),
    is_verified BIT NOT NULL CONSTRAINT DF_part_relationships_is_verified DEFAULT (0),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_part_relationships_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_part_relationships PRIMARY KEY (relationship_id),
    CONSTRAINT FK_part_relationships_pricebook_versions
        FOREIGN KEY (pricebook_version_id)
        REFERENCES rfq.pricebook_versions(pricebook_version_id),
    CONSTRAINT FK_part_relationships_parent_parts
        FOREIGN KEY (parent_part_id)
        REFERENCES rfq.parts(part_id),
    CONSTRAINT FK_part_relationships_child_parts
        FOREIGN KEY (child_part_id)
        REFERENCES rfq.parts(part_id),
    CONSTRAINT FK_part_relationships_parent_items
        FOREIGN KEY (parent_pricebook_item_id)
        REFERENCES rfq.pricebook_items(pricebook_item_id),
    CONSTRAINT FK_part_relationships_child_items
        FOREIGN KEY (child_pricebook_item_id)
        REFERENCES rfq.pricebook_items(pricebook_item_id),
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
GO

CREATE TABLE rfq.domain_synonyms (
    synonym_id BIGINT IDENTITY(1,1) NOT NULL,
    term NVARCHAR(100) NOT NULL,
    term_normalized NVARCHAR(100) NOT NULL,
    canonical_term NVARCHAR(100) NOT NULL,
    canonical_term_normalized NVARCHAR(100) NOT NULL,
    scope_key NVARCHAR(100) NOT NULL CONSTRAINT DF_domain_synonyms_scope_key DEFAULT ('global'),
    synonym_type NVARCHAR(50) NULL,
    applies_to_tool_family NVARCHAR(255) NULL,
    is_active BIT NOT NULL CONSTRAINT DF_domain_synonyms_is_active DEFAULT (1),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_domain_synonyms_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_domain_synonyms PRIMARY KEY (synonym_id)
);
GO

CREATE TABLE rfq.item_aliases (
    item_alias_id BIGINT IDENTITY(1,1) NOT NULL,
    part_id BIGINT NULL,
    pricebook_item_id BIGINT NULL,
    alias_text NVARCHAR(255) NOT NULL,
    alias_text_normalized NVARCHAR(255) NOT NULL,
    alias_type NVARCHAR(50) NULL,
    source NVARCHAR(100) NULL,
    is_active BIT NOT NULL CONSTRAINT DF_item_aliases_is_active DEFAULT (1),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_item_aliases_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_item_aliases PRIMARY KEY (item_alias_id),
    CONSTRAINT FK_item_aliases_parts
        FOREIGN KEY (part_id)
        REFERENCES rfq.parts(part_id),
    CONSTRAINT FK_item_aliases_pricebook_items
        FOREIGN KEY (pricebook_item_id)
        REFERENCES rfq.pricebook_items(pricebook_item_id),
    CONSTRAINT CK_item_aliases_has_target
        CHECK (part_id IS NOT NULL OR pricebook_item_id IS NOT NULL)
);
GO

CREATE UNIQUE INDEX UX_pricebook_versions_one_active_per_family
ON rfq.pricebook_versions(product_family)
WHERE is_active = 1;
GO

CREATE INDEX IX_pricebook_sections_version_section
ON rfq.pricebook_sections(pricebook_version_id, section_number_normalized);
GO

CREATE INDEX IX_pricebook_items_valid_candidate
ON rfq.pricebook_items(is_valid_candidate);
GO

CREATE INDEX IX_pricebook_items_assembly
ON rfq.pricebook_items(complete_assembly_number);
GO

CREATE INDEX IX_pricebook_items_source
ON rfq.pricebook_items(source_workbook, source_sheet, source_row_number);
GO

CREATE INDEX IX_pricebook_items_part_id
ON rfq.pricebook_items(part_id);
GO

CREATE INDEX IX_item_attributes_name_value
ON rfq.item_attributes(attribute_definition_id, attribute_value_normalized);
GO

CREATE INDEX IX_part_relationships_parent_part
ON rfq.part_relationships(parent_part_id);
GO

CREATE INDEX IX_part_relationships_child_part
ON rfq.part_relationships(child_part_id);
GO

CREATE UNIQUE INDEX UX_part_relationships_context
ON rfq.part_relationships(
    pricebook_version_id,
    parent_part_id,
    child_part_id,
    relationship_type_code,
    relationship_source,
    source_sheet,
    source_row_number
);
GO

CREATE INDEX IX_domain_synonyms_term_normalized
ON rfq.domain_synonyms(term_normalized);
GO

CREATE INDEX IX_domain_synonyms_canonical_term_normalized
ON rfq.domain_synonyms(canonical_term_normalized);
GO

CREATE UNIQUE INDEX UX_domain_synonyms_active_term_scope
ON rfq.domain_synonyms(
    term_normalized,
    canonical_term_normalized,
    scope_key
)
WHERE is_active = 1;
GO

CREATE INDEX IX_item_aliases_alias_text_normalized
ON rfq.item_aliases(alias_text_normalized);
GO

CREATE UNIQUE INDEX UX_item_aliases_part_alias_normalized
ON rfq.item_aliases(part_id, alias_text_normalized)
WHERE part_id IS NOT NULL;
GO

CREATE UNIQUE INDEX UX_item_aliases_pricebook_item_alias_normalized
ON rfq.item_aliases(pricebook_item_id, alias_text_normalized)
WHERE pricebook_item_id IS NOT NULL;
GO

INSERT INTO rfq.attribute_definitions (
    attribute_name,
    display_name,
    unit_hint
)
VALUES
    ('overshot_od', 'Overshot OD', 'inch'),
    ('size', 'Size', NULL),
    ('total_length', 'Total Length', 'inch'),
    ('diameter_largest_wicker', 'Diameter of Largest Wicker', 'inch'),
    ('diameter_smallest_wicker', 'Diameter of Smallest Wicker', 'inch'),
    ('catch_size', 'Catch Size', 'inch'),
    ('nominal_size_or_catch_size', 'Nominal Size or Catch Size', 'inch'),
    ('assembly_dressed_to_packoff', 'Assembly Dressed to Packoff', NULL),
    ('shoe_od', 'Shoe OD', 'inch'),
    ('hole_size', 'Hole Size', 'inch'),
    ('inside_diameter', 'Inside Diameter', 'inch');
GO

INSERT INTO rfq.relationship_type_definitions (
    relationship_type_code,
    display_name,
    description
)
VALUES
    (
        'assembly_contains_component',
        'Assembly Contains Component',
        'Parent assembly contains child component. May be derived from Complete Assembly Number.'
    ),
    (
        'cross_reference',
        'Cross Reference',
        'Part is cross-referenced to another part number or external reference.'
    ),
    (
        'alternate_part',
        'Alternate Part',
        'Part may be an alternate to another part.'
    );
GO

/*
End of Phase 1 SQL DDL Draft - Production-Oriented V1.
*/
