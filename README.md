# Customer Service Agent

A **copilot** for human customer service agents — not a fully autonomous chatbot. The agent drafts reply messages by retrieving company data, but a human always reviews, edits, and approves before anything is sent to the customer.

> **This is a human-in-the-loop system by design.** The LLM generates draft replies with confidence scores and internal notes. Human CS agents audit every draft — approving, editing, or rejecting it. The agent handles data retrieval and drafting; the human owns the final response.

## Quick Start

```bash
# 1. Install dependencies
pip install -e ".[dev]"

# 2. Set up your API key
cp .env.example .env
# Edit .env with your Anthropic API key

# 3. Start the backend
uvicorn agent.api:app --reload

# 4. Chat via CLI (in another terminal)
python -m cli --business beauty_lab --customer CUS-001
```

The CLI shows each draft for review before it's "sent." Use `--auto-approve` to skip review (for testing only).

## How It Works

1. Customer sends a message
2. Backend loads the business config and retrieves relevant data via tool calls
3. LLM generates a **draft reply** (not a final response)
4. **Human agent reviews the draft** — approve, edit, or reject
5. Only approved/edited replies are sent to the customer

The agent is fast at pulling data and composing responses. The human ensures accuracy, tone, and handles edge cases the LLM can't.

## Project Structure

```
src/
  agent/          # Backend service
    api.py        # FastAPI endpoints (POST /chat)
    loop.py       # Agent loop (LLM + tool calls)
    config.py     # Business config loader
    csv_tool.py   # CSV data lookup tool
    logging.py    # LLM call logging (JSONL)
    session.py    # Session management
  cli.py          # CLI client with draft review
configs/          # Business configs (YAML per business)
data/             # CSV data files per business
scripts/          # Data generation scripts
tests/            # Unit and e2e tests
docs/             # Component documentation
logs/             # LLM call logs (gitignored)
```

## API

### POST /chat

```json
// Request
{
  "business_id": "beauty_lab",
  "customer_id": "CUS-001",
  "message": "When is my next appointment?"
}

// Response
{
  "customer_id": "CUS-001",
  "reply": "Your next appointment is..."
}
```

The response is a **draft** — the calling application is responsible for presenting it for human review before delivering to the customer.

## Business Configs

Each business has a YAML config in `configs/` that defines:
- System prompt for the LLM
- Available data sources (CSV files with descriptions)

See `configs/beauty_lab.yaml` for an example with services, staff, appointments, customers, and reviews data.

## Test Data

The `beauty_lab` config includes synthetic test data generated from real business research:
- **200 customers** with membership tiers and prepaid balances
- **1,200+ appointments** spanning 6 months
- **5 staff members** with expertise ratings and detailed strengths/weaknesses
- **250+ customer reviews** with realistic positive and negative feedback
- **26 services** across Facial, Hair & Scalp, Eyelash, and Manicure categories

Regenerate with: `python scripts/generate_beauty_lab_data.py`

## Testing

```bash
# Unit tests
pytest tests/ --ignore=tests/test_e2e.py -v

# E2e tests (requires ANTHROPIC_API_KEY)
pytest tests/test_e2e.py -v
```

Scheduled CI runs every 10 minutes via GitHub Actions (`.github/workflows/test.yml`).

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Anthropic API key | (required) |
| `LLM_MODEL` | Model to use for the agent loop | `claude-sonnet-4-6` |

## License

MIT
