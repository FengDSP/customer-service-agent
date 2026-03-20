# Backend Service

FastAPI Python service that receives customer messages and returns AI-drafted replies.

## API

### POST /chat
Accepts a customer message and returns a draft reply.

Request:
```json
{
  "session_id": "string",
  "business_id": "string",
  "message": "string"
}
```

Response:
```json
{
  "session_id": "string",
  "reply": "string"
}
```

- `session_id` tracks a multi-turn conversation. The backend maintains conversation history per session.
- `business_id` determines which business config to load.

## Agent Loop

1. Load business config from `configs/<business_id>.yaml`.
2. Build the LLM prompt: system instructions from config + conversation history + new customer message.
3. Call the LLM. If the LLM response includes tool calls, execute them and feed results back. Repeat until the LLM produces a final text reply.
4. Log the full LLM interaction (see `docs/llm-logging.md`).
5. Return the draft reply.

## Data Tools

Data access is exposed to the LLM as tool calls. The available tools are determined by the business config.

### CSV Lookup
Reads from local CSV files. The business config specifies which CSV files are available and what they contain (e.g., orders, products, customers). The tool accepts a query description and returns matching rows.

Tool definition and implementation details will evolve as the agent loop is built.

## Business Config

Each business has a YAML file in `configs/`. See `docs/business-config.md` for the format.

## Session Storage

Conversation history is stored in memory for now. Sessions are lost on restart. Persistent storage is out of scope until cloud hosting.
