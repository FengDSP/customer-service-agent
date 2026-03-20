from agent.config import load_business_config
from agent.prompt import build_user_prompt


def _config():
    return load_business_config("acme_retail")


def test_prompt_contains_customer_message():
    prompt = build_user_prompt("Where is my order?", [], _config(), "alice@example.com")
    assert "<customer_message>" in prompt
    assert "Where is my order?" in prompt
    assert "</customer_message>" in prompt


def test_prompt_contains_metadata():
    prompt = build_user_prompt("Hi", [], _config(), "alice@example.com")
    assert "<customer_id>alice@example.com</customer_id>" in prompt
    assert "<business_id>acme_retail</business_id>" in prompt
    assert "<business_name>Acme Retail Support</business_name>" in prompt
    assert "<current_time>" in prompt


def test_prompt_contains_json_format():
    prompt = build_user_prompt("Hi", [], _config(), "cust1")
    assert "draft_reply" in prompt
    assert "internal_note" in prompt
    assert "confidence" in prompt
    assert "needs_human_review" in prompt
    assert "suggested_actions" in prompt


def test_prompt_includes_history():
    history = [
        {"role": "user", "content": "Hello", "timestamp": "2026-03-20T10:00:00"},
        {"role": "assistant", "content": "Hi there!", "timestamp": "2026-03-20T10:00:05"},
    ]
    prompt = build_user_prompt("Follow up", history, _config(), "cust1")
    assert "<conversation_history" in prompt
    assert "customer: Hello" in prompt
    assert "agent: Hi there!" in prompt


def test_prompt_no_history_section_when_empty():
    prompt = build_user_prompt("Hi", [], _config(), "cust1")
    assert "<conversation_history" not in prompt


def test_prompt_windows_long_history():
    history = [
        {"role": "user", "content": f"msg {i}"}
        for i in range(30)
    ]
    prompt = build_user_prompt("new msg", history, _config(), "cust1")
    assert "<older_conversation_summary>" in prompt
    assert "10 earlier messages" in prompt
    assert 'showing="last 20"' in prompt


def test_prompt_session_start_from_timestamp():
    history = [
        {"role": "user", "content": "first", "timestamp": "2026-03-18T09:00:00"},
        {"role": "assistant", "content": "reply"},
    ]
    prompt = build_user_prompt("new", history, _config(), "cust1")
    assert "<session_start>2026-03-18T09:00:00</session_start>" in prompt
