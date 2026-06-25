# Data Dictionary

## Purpose

This document describes the main data concepts used by the AI RFQ Agent.

## Pricebook Version

Represents one approved version of the Fishing Tools pricebook.

Example:

- Fishing Tools PB 2022 Jun
- Working File FINAL 004

## Part

A unique approved part number.

Important rule:

Part numbers must be stored as text, not numbers.

Reason:

Part numbers may contain letters, slashes, suffixes, leading zeros, or special characters.

## Pricebook Item

A part number in a specific pricebook context.

The same part number may appear multiple times in different sections or product contexts.

Do not overwrite duplicates.

## Section

A pricebook section or product grouping.

Examples may include tool family, section number, or sheet context.

## Item Attribute

Flexible technical properties for an item.

Examples:

- OD
- size
- connection
- tool family
- item role
- assembly number

## Search Text

A generated human-readable text field used for keyword search and embeddings.

It should combine useful fields such as:

- part number
- description
- section
- tool family
- attributes
- source context

## Source Traceability

Every searchable item must preserve where it came from.

Minimum traceability fields:

- pricebook version
- source workbook
- source sheet
- source row or context
