# Evaluation

## Purpose

Evaluation proves whether the RFQ Agent is useful and safe.

## Core Metrics

- Top-1 accuracy
- Recall at 3
- Recall at 5
- Mean reciprocal rank
- no-invention rate
- latency
- cost
- user feedback rate

## Most Important Metric

No-invention rate must be 100 percent.

The system must never output a part number that was not retrieved from approved SQL Server data.

## Golden Dataset

A golden dataset is a set of RFQ examples reviewed by a subject matter expert.

Each row should include:

- rfq_text
- rfq_line
- expected_part_number
- expected_tool_family
- notes
- difficulty
- reviewer

## Evaluation Rule

Do not rely only on impressive demos.

The system must be tested against known RFQs before pilot rollout.
