# Customer Service Agent

A customer service copilot that drafts reply messages by autonomously retrieving company data. Human agents approve or modify drafts before sending.

The agent receives a customer message, runs an LLM-powered loop that pulls relevant business data via tool calls, and returns a draft reply.

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
python -m cli --business beauty_lab
```

## Project Structure

```
src/
  agent/          # Backend service
    api.py        # FastAPI endpoints (POST /chat)
    loop.py       # Agent loop (LLM + tool calls)
    config.py     # Business config loader
    csv_tool.py   # CSV data lookup tool
    logging.py    # LLM call logging
    session.py    # Session management
  cli.py          # CLI client
configs/          # Business configs (YAML per business)
data/             # CSV data files per business
scripts/          # Data generation scripts
tests/            # Unit and e2e tests
docs/             # Component documentation
logs/             # LLM call logs (gitignored)
```

## How It Works

1. Customer sends a message via CLI (or API directly)
2. Backend loads the business config (`configs/<business_id>.yaml`)
3. Agent loop sends the conversation to Claude with business-specific tools
4. If Claude makes tool calls (e.g., CSV lookup), they execute and feed results back
5. Loop repeats until Claude produces a final text reply
6. Draft reply is returned to the caller

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
