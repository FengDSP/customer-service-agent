# LLM Logging

All LLM API calls made by the backend agent loop are logged locally for debugging and future evaluation.

## Log Location

Logs are written to `logs/llm/` with one JSON file per agent loop invocation.

Filename format: `{session_id}_{timestamp}.json`

## Log Format

```json
{
  "session_id": "string",
  "business_id": "string",
  "timestamp": "ISO 8601",
  "turns": [
    {
      "role": "system | user | assistant | tool",
      "content": "string",
      "tool_calls": [],
      "tool_results": []
    }
  ],
  "model": "string",
  "usage": {
    "input_tokens": 0,
    "output_tokens": 0
  }
}
```

Each file captures the full conversation sent to the LLM, including all tool call rounds, the final response, and token usage.

## Purpose

- Debugging: inspect what the LLM saw and how it responded.
- Evaluation: replay logs to test prompt or tool changes against historical conversations.
- The planned eval portal will read from this directory.
