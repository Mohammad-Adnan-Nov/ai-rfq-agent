/*
AI RFQ Agent - Pricebook Foundation Tables
Phase 1 SQL DDL Draft

Purpose:
Create SQL Server tables for approved Fishing Tool pricebook data.

Important governance rules:
- SQL Server is the source of truth.
- Part numbers must be stored as text.
- Qdrant is only semantic retrieval.
- OpenAI must not invent part numbers.
- RFQ runtime tables are not included in this migration.
*/

SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;
GO

CREATE TABLE dbo.pricebook_versions (
    pricebook_version_id BIGINT IDENTITY(1,1) NOT NULL,
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

CREATE TABLE dbo.pricebook_sections (
    section_id BIGINT IDENTITY(1,1) NOT NULL,
    pricebook_version_id BIGINT NOT NULL,
    section_number NVARCHAR(50) NOT NULL,
    sheet_number NVARCHAR(50) NULL,
    title NVARCHAR(255) NULL,
    source_sheet NVARCHAR(255) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_pricebook_sections_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_pricebook_sections PRIMARY KEY (section_id),
    CONSTRAINT FK_pricebook_sections_pricebook_versions
        FOREIGN KEY (pricebook_version_id)
        REFERENCES dbo.pricebook_versions(pricebook_version_id),
    CONSTRAINT UQ_pricebook_sections_context
        UNIQUE (pricebook_version_id, section_number, sheet_number, title)
);
GO

CREATE TABLE dbo.parts (
    part_id BIGINT IDENTITY(1,1) NOT NULL,
    part_number NVARCHAR(100) NOT NULL,
    part_number_normalized NVARCHAR(100) NOT NULL,
    is_placeholder BIT NOT NULL CONSTRAINT DF_parts_is_placeholder DEFAULT (0),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_parts_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_parts PRIMARY KEY (part_id),
    CONSTRAINT UQ_parts_part_number_normalized UNIQUE (part_number_normalized)
);
GO

CREATE TABLE dbo.pricebook_items (
    pricebook_item_id BIGINT IDENTITY(1,1) NOT NULL,
    pricebook_version_id BIGINT NOT NULL,
    section_id BIGINT NULL,
    part_id BIGINT NOT NULL,
    description NVARCHAR(500) NULL,
    logan_part_number NVARCHAR(100) NULL,
    logan_description NVARCHAR(500) NULL,
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
        REFERENCES dbo.pricebook_versions(pricebook_version_id),
    CONSTRAINT FK_pricebook_items_pricebook_sections
        FOREIGN KEY (section_id)
        REFERENCES dbo.pricebook_sections(section_id),
    CONSTRAINT FK_pricebook_items_parts
        FOREIGN KEY (part_id)
        REFERENCES dbo.parts(part_id)
);
GO

CREATE TABLE dbo.attribute_definitions (
    attribute_definition_id BIGINT IDENTITY(1,1) NOT NULL,
    attribute_name NVARCHAR(100) NOT NULL,
    display_name NVARCHAR(255) NOT NULL,
    unit_hint NVARCHAR(50) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_attribute_definitions_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_attribute_definitions PRIMARY KEY (attribute_definition_id),
    CONSTRAINT UQ_attribute_definitions_attribute_name UNIQUE (attribute_name)
);
GO

CREATE TABLE dbo.item_attributes (
    item_attribute_id BIGINT IDENTITY(1,1) NOT NULL,
    pricebook_item_id BIGINT NOT NULL,
    attribute_definition_id BIGINT NOT NULL,
    attribute_value_text NVARCHAR(255) NOT NULL,
    attribute_value_normalized NVARCHAR(255) NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_item_attributes_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_item_attributes PRIMARY KEY (item_attribute_id),
    CONSTRAINT FK_item_attributes_pricebook_items
        FOREIGN KEY (pricebook_item_id)
        REFERENCES dbo.pricebook_items(pricebook_item_id),
    CONSTRAINT FK_item_attributes_attribute_definitions
        FOREIGN KEY (attribute_definition_id)
        REFERENCES dbo.attribute_definitions(attribute_definition_id),
    CONSTRAINT UQ_item_attributes_item_attribute_value
        UNIQUE (pricebook_item_id, attribute_definition_id, attribute_value_text)
);
GO

CREATE TABLE dbo.item_search_index (
    item_search_index_id BIGINT IDENTITY(1,1) NOT NULL,
    pricebook_item_id BIGINT NOT NULL,
    search_text NVARCHAR(MAX) NOT NULL,
    search_text_version NVARCHAR(50) NOT NULL,
    created_at DATETIME2 NOT NULL CONSTRAINT DF_item_search_index_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_item_search_index PRIMARY KEY (item_search_index_id),
    CONSTRAINT FK_item_search_index_pricebook_items
        FOREIGN KEY (pricebook_item_id)
        REFERENCES dbo.pricebook_items(pricebook_item_id),
    CONSTRAINT UQ_item_search_index_pricebook_item UNIQUE (pricebook_item_id)
);
GO

CREATE TABLE dbo.ingestion_runs (
    ingestion_run_id BIGINT IDENTITY(1,1) NOT NULL,
    pricebook_version_id BIGINT NULL,
    source_workbook_name NVARCHAR(255) NOT NULL,
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
        REFERENCES dbo.pricebook_versions(pricebook_version_id)
);
GO

CREATE TABLE dbo.part_relationships (
    relationship_id BIGINT IDENTITY(1,1) NOT NULL,
    pricebook_version_id BIGINT NOT NULL,
    parent_part_id BIGINT NOT NULL,
    child_part_id BIGINT NOT NULL,
    parent_pricebook_item_id BIGINT NULL,
    child_pricebook_item_id BIGINT NULL,
    relationship_type NVARCHAR(100) NOT NULL,
    relationship_source NVARCHAR(100) NOT NULL,
    source_sheet NVARCHAR(255) NULL,
    source_row_number INT NULL,
    confidence_level NVARCHAR(50) NOT NULL CONSTRAINT DF_part_relationships_confidence_level DEFAULT ('derived'),
    is_verified BIT NOT NULL CONSTRAINT DF_part_relationships_is_verified DEFAULT (0),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_part_relationships_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_part_relationships PRIMARY KEY (relationship_id),
    CONSTRAINT FK_part_relationships_pricebook_versions
        FOREIGN KEY (pricebook_version_id)
        REFERENCES dbo.pricebook_versions(pricebook_version_id),
    CONSTRAINT FK_part_relationships_parent_parts
        FOREIGN KEY (parent_part_id)
        REFERENCES dbo.parts(part_id),
    CONSTRAINT FK_part_relationships_child_parts
        FOREIGN KEY (child_part_id)
        REFERENCES dbo.parts(part_id),
    CONSTRAINT FK_part_relationships_parent_items
        FOREIGN KEY (parent_pricebook_item_id)
        REFERENCES dbo.pricebook_items(pricebook_item_id),
    CONSTRAINT FK_part_relationships_child_items
        FOREIGN KEY (child_pricebook_item_id)
        REFERENCES dbo.pricebook_items(pricebook_item_id)
);
GO

CREATE TABLE dbo.domain_synonyms (
    synonym_id BIGINT IDENTITY(1,1) NOT NULL,
    term NVARCHAR(100) NOT NULL,
    canonical_term NVARCHAR(100) NOT NULL,
    synonym_type NVARCHAR(50) NULL,
    applies_to_tool_family NVARCHAR(255) NULL,
    is_active BIT NOT NULL CONSTRAINT DF_domain_synonyms_is_active DEFAULT (1),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_domain_synonyms_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_domain_synonyms PRIMARY KEY (synonym_id)
);
GO

CREATE TABLE dbo.item_aliases (
    item_alias_id BIGINT IDENTITY(1,1) NOT NULL,
    part_id BIGINT NULL,
    pricebook_item_id BIGINT NULL,
    alias_text NVARCHAR(255) NOT NULL,
    alias_type NVARCHAR(50) NULL,
    source NVARCHAR(100) NULL,
    is_active BIT NOT NULL CONSTRAINT DF_item_aliases_is_active DEFAULT (1),
    created_at DATETIME2 NOT NULL CONSTRAINT DF_item_aliases_created_at DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_item_aliases PRIMARY KEY (item_alias_id),
    CONSTRAINT FK_item_aliases_parts
        FOREIGN KEY (part_id)
        REFERENCES dbo.parts(part_id),
    CONSTRAINT FK_item_aliases_pricebook_items
        FOREIGN KEY (pricebook_item_id)
        REFERENCES dbo.pricebook_items(pricebook_item_id),
    CONSTRAINT CK_item_aliases_has_target
        CHECK (part_id IS NOT NULL OR pricebook_item_id IS NOT NULL)
);
GO

CREATE INDEX IX_parts_part_number_normalized
ON dbo.parts(part_number_normalized);
GO

CREATE INDEX IX_pricebook_items_valid_candidate
ON dbo.pricebook_items(is_valid_candidate);
GO

CREATE INDEX IX_pricebook_items_assembly
ON dbo.pricebook_items(complete_assembly_number);
GO

CREATE INDEX IX_pricebook_items_source
ON dbo.pricebook_items(source_workbook, source_sheet, source_row_number);
GO

CREATE INDEX IX_pricebook_items_part_id
ON dbo.pricebook_items(part_id);
GO

CREATE INDEX IX_item_attributes_name_value
ON dbo.item_attributes(attribute_definition_id, attribute_value_normalized);
GO

CREATE INDEX IX_part_relationships_parent_part
ON dbo.part_relationships(parent_part_id);
GO

CREATE INDEX IX_part_relationships_child_part
ON dbo.part_relationships(child_part_id);
GO

CREATE INDEX IX_domain_synonyms_term
ON dbo.domain_synonyms(term);
GO

CREATE INDEX IX_item_aliases_alias_text
ON dbo.item_aliases(alias_text);
GO

/*
End of Phase 1 SQL DDL Draft.
*/
