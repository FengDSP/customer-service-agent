"""Tests for admin API endpoints."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from agent.api import app

client = TestClient(app)

SAMPLE_LOG_1 = {
    "customer_id": "CUS-001",
    "business_id": "test_biz",
    "timestamp": "2026-03-20T10:00:00+00:00",
    "system_prompt": "You are a helpful agent.",
    "turns": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": [{"type": "text", "text": "Hi there!"}]},
    ],
    "model": "claude-sonnet-4-6",
    "usage": {"input_tokens": 100, "output_tokens": 30},
}

SAMPLE_LOG_2 = {
    "customer_id": "CUS-001",
    "business_id": "test_biz",
    "timestamp": "2026-03-21T14:00:00+00:00",
    "system_prompt": "You are a helpful agent.",
    "turns": [
        {"role": "user", "content": "Book an appointment"},
        {
            "role": "assistant",
            "content": [
                {
                    "type": "tool_use",
                    "id": "t1",
                    "name": "lookup_appointments",
                    "input": {"query": "available"},
                },
            ],
        },
        {
            "role": "user",
            "content": [
                {"type": "tool_result", "tool_use_id": "t1", "content": "March 25 at 10am"}
            ],
        },
        {
            "role": "assistant",
            "content": [{"type": "text", "text": "I found a slot on March 25 at 10am."}],
        },
    ],
    "model": "claude-sonnet-4-6",
    "usage": {"input_tokens": 250, "output_tokens": 60},
}

SAMPLE_LOG_CUS002 = {
    "customer_id": "CUS-002",
    "business_id": "test_biz",
    "timestamp": "2026-03-19T09:00:00+00:00",
    "system_prompt": "You are a helpful agent.",
    "turns": [
        {"role": "user", "content": "What are your hours?"},
        {"role": "assistant", "content": [{"type": "text", "text": "We are open 10am-6pm."}]},
    ],
    "model": "claude-sonnet-4-6",
    "usage": {"input_tokens": 80, "output_tokens": 20},
}


def _create_temp_logs(tmp_path: Path):
    biz_dir = tmp_path / "test_biz"
    biz_dir.mkdir(parents=True)

    with open(biz_dir / "CUS-001.jsonl", "w") as f:
        f.write(json.dumps(SAMPLE_LOG_1) + "\n")
        f.write(json.dumps(SAMPLE_LOG_2) + "\n")

    with open(biz_dir / "CUS-002.jsonl", "w") as f:
        f.write(json.dumps(SAMPLE_LOG_CUS002) + "\n")


# --- GET /admin/logs/{business_id}/customers ---


def test_admin_list_customers():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _create_temp_logs(tmp_path)
        with patch("agent.log_reader.LOGS_DIR", tmp_path):
            resp = client.get("/admin/logs/test_biz/customers")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # Sorted by last_interaction desc — CUS-001 is more recent
    assert data[0]["customer_id"] == "CUS-001"
    assert data[0]["total_interactions"] == 2
    assert data[0]["total_tokens"]["input"] == 350
    assert data[1]["customer_id"] == "CUS-002"


def test_admin_list_customers_empty():
    with tempfile.TemporaryDirectory() as tmp:
        with patch("agent.log_reader.LOGS_DIR", Path(tmp)):
            resp = client.get("/admin/logs/nonexistent/customers")

    assert resp.status_code == 200
    assert resp.json() == []


# --- GET /admin/logs/{business_id}/{customer_id} ---


def test_admin_list_log_entries():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _create_temp_logs(tmp_path)
        with patch("agent.log_reader.LOGS_DIR", tmp_path):
            resp = client.get("/admin/logs/test_biz/CUS-001")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    # Sorted by timestamp desc
    assert data[0]["timestamp"] == "2026-03-21T14:00:00+00:00"
    assert data[0]["customer_message"] == "Book an appointment"
    assert "March 25" in data[0]["draft_reply"]
    assert data[0]["turns_count"] == 4
    assert data[1]["customer_message"] == "Hello"


def test_admin_list_log_entries_empty():
    with tempfile.TemporaryDirectory() as tmp:
        with patch("agent.log_reader.LOGS_DIR", Path(tmp)):
            resp = client.get("/admin/logs/test_biz/CUS-999")

    assert resp.status_code == 200
    assert resp.json() == []


# --- GET /admin/logs/{business_id}/{customer_id}/{log_index} ---


def test_admin_get_log_entry():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _create_temp_logs(tmp_path)
        with patch("agent.log_reader.LOGS_DIR", tmp_path):
            resp = client.get("/admin/logs/test_biz/CUS-001/1")

    assert resp.status_code == 200
    data = resp.json()
    assert data["index"] == 1
    assert data["timestamp"] == "2026-03-21T14:00:00+00:00"
    assert len(data["turns"]) == 4
    # Multi-turn: 2 LLM calls (tool_use response + final response)
    assert len(data["llm_calls"]) == 2
    assert data["llm_calls"][0]["call_index"] == 0
    assert data["llm_calls"][1]["call_index"] == 1


def test_admin_get_log_entry_first():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _create_temp_logs(tmp_path)
        with patch("agent.log_reader.LOGS_DIR", tmp_path):
            resp = client.get("/admin/logs/test_biz/CUS-001/0")

    assert resp.status_code == 200
    data = resp.json()
    assert data["index"] == 0
    # Simple turn: 1 LLM call
    assert len(data["llm_calls"]) == 1


def test_admin_get_log_entry_not_found():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _create_temp_logs(tmp_path)
        with patch("agent.log_reader.LOGS_DIR", tmp_path):
            resp = client.get("/admin/logs/test_biz/CUS-001/99")

    assert resp.status_code == 404


# --- POST /admin/replay ---


@patch("agent.api.anthropic.Anthropic")
def test_admin_replay(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    mock_block = MagicMock()
    mock_block.text = "Replayed response text"
    mock_block.type = "text"

    mock_response = MagicMock()
    mock_response.content = [mock_block]
    mock_response.usage.input_tokens = 150
    mock_response.usage.output_tokens = 40

    mock_client.messages.create.return_value = mock_response

    resp = client.post(
        "/admin/replay",
        json={
            "model": "claude-sonnet-4-6",
            "system": "You are a helpful agent.",
            "messages": [{"role": "user", "content": "Hello"}],
            "tools": [],
            "original_response_text": "Original response text",
        },
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["original"]["text"] == "Original response text"
    assert data["replayed"]["text"] == "Replayed response text"
    assert data["replayed"]["usage"]["input_tokens"] == 150
    assert data["replayed"]["usage"]["output_tokens"] == 40

    mock_client.messages.create.assert_called_once()
    call_kwargs = mock_client.messages.create.call_args[1]
    assert call_kwargs["model"] == "claude-sonnet-4-6"
    assert call_kwargs["system"] == "You are a helpful agent."


@patch("agent.api.anthropic.Anthropic")
def test_admin_replay_error(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.side_effect = Exception("API error")

    resp = client.post(
        "/admin/replay",
        json={
            "model": "claude-sonnet-4-6",
            "system": "test",
            "messages": [{"role": "user", "content": "hi"}],
            "original_response_text": "original",
        },
    )

    assert resp.status_code == 500
