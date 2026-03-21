from agent.config import load_business_config
from agent.csv_tool import build_tool_definitions, execute_csv_lookup, execute_grep


def _config():
    return load_business_config("acme_retail")


def _beauty_config():
    return load_business_config("beauty_lab")


def test_build_tool_definitions():
    tools = build_tool_definitions(_config())
    # 2 lookup tools + 1 grep tool
    assert len(tools) == 3
    assert tools[0]["name"] == "lookup_orders"
    assert tools[1]["name"] == "lookup_products"
    assert tools[2]["name"] == "grep_data"
    assert "input_schema" in tools[0]


def test_tool_descriptions_include_metadata():
    tools = build_tool_definitions(_config())
    desc = tools[0]["description"]
    assert "rows" in desc
    assert "KB" in desc or "B" in desc
    assert "e.g." in desc


def test_beauty_lab_tools():
    tools = build_tool_definitions(_beauty_config())
    # 5 lookup tools + 1 grep
    assert len(tools) == 6
    names = [t["name"] for t in tools]
    assert "lookup_services" in names
    assert "lookup_staff" in names
    assert "lookup_appointments" in names
    assert "lookup_customers" in names
    assert "lookup_reviews" in names
    assert "grep_data" in names


def test_lookup_by_column_value():
    result = execute_csv_lookup(
        _config(),
        "lookup_orders",
        {
            "column": "customer_email",
            "value": "alice@example.com",
        },
    )
    assert "alice@example.com" in result
    assert "ORD-1001" in result
    assert "ORD-1003" in result


def test_lookup_by_keyword():
    result = execute_csv_lookup(
        _config(),
        "lookup_products",
        {
            "keyword": "Widget",
        },
    )
    assert "Blue Widget" in result
    assert "Green Widget" in result


def test_lookup_no_match():
    result = execute_csv_lookup(
        _config(),
        "lookup_orders",
        {
            "column": "customer_email",
            "value": "nobody@example.com",
        },
    )
    assert "No matching" in result


def test_lookup_invalid_column():
    result = execute_csv_lookup(
        _config(),
        "lookup_orders",
        {
            "column": "nonexistent",
            "value": "test",
        },
    )
    assert "Error" in result


def test_lookup_unknown_source():
    result = execute_csv_lookup(_config(), "lookup_unknown", {})
    assert "Error" in result


def test_lookup_no_filter_returns_all():
    result = execute_csv_lookup(_config(), "lookup_products", {})
    assert "Blue Widget" in result
    assert "Premium Gadget" in result


def test_grep_across_files():
    result = execute_grep(_config(), {"query": "alice@example.com"})
    assert "orders" in result
    assert "alice@example.com" in result


def test_grep_scoped_to_source():
    result = execute_grep(
        _config(),
        {
            "query": "Widget",
            "sources": ["products"],
        },
    )
    assert "products" in result
    assert "Blue Widget" in result


def test_grep_no_match():
    result = execute_grep(_config(), {"query": "zzz_nonexistent_zzz"})
    assert "No matches" in result


def test_grep_beauty_lab():
    result = execute_grep(
        _beauty_config(),
        {
            "query": "Lily Chen",
            "sources": ["staff"],
        },
    )
    assert "Lily Chen" in result
