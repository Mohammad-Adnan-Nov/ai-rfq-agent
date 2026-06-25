# Architecture

## Project

AI RFQ Agent for NOV Downhole / Fishing Tools.

## Purpose

This system helps sales users identify approved Fishing Tool part numbers from messy RFQ text.

It is a retrieval and decision-support system, not an auto-quoting system.

## Core Architecture

The target architecture is retrieval-first:

RFQ text
-> RFQ extraction
-> deterministic normalization
-> SQL Server retrieval
-> Qdrant semantic retrieval
-> candidate ranking
-> OpenAI candidate validation
-> output guardrail
-> sales-facing result table

## Source of Truth

SQL Server is the source of truth for approved part numbers.

Qdrant is not the source of truth.

OpenAI is not the source of truth.

## Main Components

- Streamlit: pilot user interface
- FastAPI: backend API boundary
- LangGraph: controlled workflow orchestration
- SQL Server: approved part-number database
- Qdrant: semantic retrieval index
- OpenAI API: RFQ extraction, embeddings, candidate validation
- MLflow: tracking, evaluation, prompt/model/search versioning
- Docker Compose: local and pilot deployment

## Current Implementation Rule

Do not build Qdrant, OpenAI workflow, LangGraph, FastAPI, or Streamlit before the data foundation is ready.

The first engineering milestone is:

Excel pricebook -> SQL-ready structured dataset -> source traceability -> search_text -> data quality report.
