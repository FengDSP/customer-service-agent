# Business Config

Each supported business has a YAML config file in `configs/`. The config tells the agent loop how to behave for that business.

## Format

```yaml
business_id: "acme_retail"
name: "Acme Retail Support"

# System-level instructions for the LLM
system_prompt: |
  You are a customer service agent for Acme Retail.
  Be polite, concise, and helpful.
  Always check order status before responding to order-related questions.

# Data sources available as LLM tool calls
data_sources:
  - name: "orders"
    type: "csv"
    path: "data/acme/orders.csv"
    description: "Customer orders with order ID, status, date, and items."
  - name: "products"
    type: "csv"
    path: "data/acme/products.csv"
    description: "Product catalog with SKU, name, price, and availability."
```

## Fields

- `business_id` — Unique identifier. Matches the filename (e.g., `configs/acme_retail.yaml`).
- `name` — Display name for the business.
- `system_prompt` — Natural language instructions injected as the LLM system prompt. This is where business-specific tone, policies, and rules are defined.
- `data_sources` — List of data sources the LLM can query via tool calls. Each entry has a name, type, file path, and a natural language description that helps the LLM understand when to use it.
