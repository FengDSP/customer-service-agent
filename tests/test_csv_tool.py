from agent.config import load_business_config
from agent.csv_tool import build_tool_definitions, execute_csv_lookup


def _config():
    return load_business_config("acme_retail")


def test_build_tool_definitions():
    tools = build_tool_definitions(_config())
    assert len(tools) == 2
    assert tools[0]["name"] == "lookup_orders"
    assert tools[1]["name"] == "lookup_products"
    assert "input_schema" in tools[0]


def test_lookup_by_column_value():
    result = execute_csv_lookup(_config(), "lookup_orders", {
        "column": "customer_email",
        "value": "alice@example.com",
    })
    assert "alice@example.com" in result
    assert "ORD-1001" in result
    assert "ORD-1003" in result


def test_lookup_by_keyword():
    result = execute_csv_lookup(_config(), "lookup_products", {
        "keyword": "Widget",
    })
    assert "Blue Widget" in result
    assert "Green Widget" in result


def test_lookup_no_match():
    result = execute_csv_lookup(_config(), "lookup_orders", {
        "column": "customer_email",
        "value": "nobody@example.com",
    })
    assert "No matching" in result


def test_lookup_invalid_column():
    result = execute_csv_lookup(_config(), "lookup_orders", {
        "column": "nonexistent",
        "value": "test",
    })
    assert "Error" in result


def test_lookup_unknown_source():
    result = execute_csv_lookup(_config(), "lookup_unknown", {})
    assert "Error" in result


def test_lookup_no_filter_returns_all():
    result = execute_csv_lookup(_config(), "lookup_products", {})
    assert "Blue Widget" in result
    assert "Premium Gadget" in result
