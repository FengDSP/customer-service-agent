# LLM Logging

All LLM API calls made by the backend agent loop are logged locally for debugging and future evaluation.

## Log Location

Logs are written to `logs/llm/{business_id}/{customer_id}.jsonl`.

Each business gets its own directory. Each customer gets a single JSONL file that accumulates all interactions over time (append-only).

```
logs/llm/
  beauty_lab/
    CUS-001.jsonl
    CUS-002.jsonl
  acme_retail/
    alice@example.com.jsonl
```

## Log Format

Each line is a self-contained JSON object representing one agent loop invocation:

```json
{"customer_id":"CUS-001","business_id":"beauty_lab","timestamp":"2026-03-20T19:30:00+00:00","system_prompt":"...","turns":[{"role":"user","content":"..."},{"role":"assistant","content":"..."}],"model":"claude-sonnet-4-6","usage":{"input_tokens":500,"output_tokens":150}}
```

Fields per line:
- `customer_id` — who the conversation is with
- `business_id` — which business config was used
- `timestamp` — ISO 8601 UTC
- `system_prompt` — the system prompt sent to the LLM
- `turns` — full conversation including tool calls and results
- `model` — LLM model used
- `usage` — token counts

## Reading Logs

```bash
# View all interactions for a customer
cat logs/llm/beauty_lab/CUS-001.jsonl | jq .

# Count interactions
wc -l logs/llm/beauty_lab/CUS-001.jsonl

# Filter by date
cat logs/llm/beauty_lab/CUS-001.jsonl | jq 'select(.timestamp > "2026-03-20")'

# Load in Python
import json
with open("logs/llm/beauty_lab/CUS-001.jsonl") as f:
    interactions = [json.loads(line) for line in f]
```

## Purpose

- Debugging: inspect what the LLM saw and how it responded.
- Evaluation: replay logs to test prompt or tool changes against historical conversations.
- The planned eval portal will read from this directory.
