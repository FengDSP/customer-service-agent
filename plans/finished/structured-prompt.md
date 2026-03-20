# Plan: Structured User Prompt with Metadata and JSON Response

## Goal
Replace the current raw message-passing approach with a structured user prompt template that provides the LLM with rich context (metadata, conversation history, timestamps) and expects a structured JSON response.

## Context
- `src/agent/loop.py` — current agent loop passes raw messages as conversation history
- `configs/acme_retail.yaml` — business config with system prompt
- `docs/backend.md` — API spec

## Design

### User Prompt Template

Each LLM call sends a single structured user prompt (not raw conversation history):

```
Draft the customer service reply message. A human customer service agent will audit your draft before sending.

<customer_message>
{the new customer message}
</customer_message>

<conversation_history count="{n}" showing="last 20">
[{timestamp}] customer: {text}
[{timestamp}] agent: {text}
...
</conversation_history>

<older_conversation_summary>
{LLM-generated summary of messages beyond the last 20, if any}
</older_conversation_summary>

<metadata>
  <customer_id>{customer_id}</customer_id>
  <business_id>{business_id}</business_id>
  <business_name>{business_name}</business_name>
  <current_time>{ISO 8601 local time}</current_time>
  <total_messages>{total message count in session}</total_messages>
  <session_start>{timestamp of first message}</session_start>
</metadata>

Respond with a JSON object in this exact format:
{
  "draft_reply": "your reply message to the customer",
  "internal_note": "optional note for the human reviewer about your reasoning or flagged issues",
  "confidence": "high | medium | low",
  "needs_human_review": true/false,
  "suggested_actions": ["optional list of follow-up actions"]
}
```

### Metadata fields to include
- **customer_id** — who we're talking to
- **business_id** / **business_name** — which business context
- **current_time** — local time so LLM can reason about dates, business hours, SLAs
- **total_messages** — conversation length for context
- **session_start** — when the conversation began (derived from first message timestamp)

### Conversation history handling
- Show the **last 20 messages** with timestamps and sender labels
- If more than 20 messages exist, generate a summary of the older messages (can be done by a separate LLM call or a simple concatenation for v1)
- Timestamps come from session history (need to add timestamps to stored messages)

### JSON response format
- **draft_reply** — the actual reply text to show to the customer
- **internal_note** — reasoning or flags for the human reviewer (not shown to customer)
- **confidence** — self-assessed confidence level
- **needs_human_review** — flag for cases the LLM is uncertain about
- **suggested_actions** — e.g., "escalate to manager", "send refund", "follow up in 2 days"

## Tasks

### Add timestamps to messages
- [x] Store timestamps with each message in session history (`{"role": "...", "content": "...", "timestamp": "..."}`)
- [x] Update `append_message` and session loading to handle the timestamp field

### Build prompt template
- [x] Create `src/agent/prompt.py` with a function that builds the structured user prompt from: customer message, history, config, customer_id, current time
- [x] Implement the last-20-messages windowing
- [x] For v1, summarize older messages by concatenating them into a brief text block (no separate LLM call yet)

### Update agent loop
- [x] Change the agent loop to send a single structured user message (from the template) instead of raw conversation history
- [x] The system prompt stays in the system field (business-specific instructions)
- [x] Parse the JSON response to extract `draft_reply` and other fields
- [x] Store the full structured response in the session and logs

### Update API response
- [x] Extend `ChatResponse` to include `internal_note`, `confidence`, `needs_human_review`, `suggested_actions`
- [x] Keep `reply` as the primary field (mapped from `draft_reply`)

### Update tests
- [x] Unit tests for the prompt builder
- [x] Update API tests for new response shape
- [x] Update e2e test assertions

### Update docs
- [x] Document the prompt template format in `docs/backend.md`
- [x] Document the JSON response schema

## Notes
- The system prompt (from business config) remains separate — it defines tone, policies, etc.
- The structured user prompt provides context; the system prompt provides instructions.
- Tool calls still work — the LLM can call tools before producing the final JSON response.
