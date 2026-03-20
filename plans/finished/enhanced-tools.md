# Plan: Enhanced Tool Calling with Data Metadata and Grep Tool

## Goal
Improve tool definitions with file metadata (row count, size, column descriptions) so the LLM makes better tool call decisions. Add a grep tool for flexible multi-file searching. Test with a beauty_lab booking scenario where the customer requests a specific staff + time and the agent suggests an alternative.

## Context
- `src/agent/csv_tool.py` — current tool implementation
- `configs/beauty_lab.yaml` — beauty lab with 5 data files (services, staff, appointments, customers, reviews)

## Tasks

### Enrich tool definitions with metadata
- [x] Include row count and file size in each tool description
- [x] Include column names with sample values in tool descriptions
- [x] This helps the LLM understand data scale and decide which columns to filter on

### Add grep tool
- [x] Create a `grep_data` tool that searches across all data files for a business
- [x] Accepts a search term, optionally scoped to specific data sources
- [x] Returns matching lines with source file context
- [x] Useful when the LLM doesn't know which file to look in

### E2E test: booking scenario
- [x] Test scenario: customer asks to book with a specific staff member at a specific time
- [x] The staff is already booked at that time (visible in appointments.csv)
- [x] The agent should look up the staff's schedule, check availability, and suggest an alternative time
- [x] Verify the draft reply contains a time suggestion

## Notes
- Branch: `worktree-backend`
- beauty_lab data: 5 staff, 26 services, 1239 appointments, 200 customers, 254 reviews
