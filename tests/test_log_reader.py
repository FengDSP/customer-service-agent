import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from agent.log_reader import (
    get_log_entry,
    list_customers_with_logs,
    list_log_entries,
)

SAMPLE_LOG_ENTRY = {
    "customer_id": "CUS-001",
    "business_id": "test_biz",
    "timestamp": "2026-03-20T19:30:00+00:00",
    "system_prompt": "You are a helpful agent.",
    "turns": [
        {"role": "user", "content": "What are your hours?"},
        {
            "role": "assistant",
            "content": [{"type": "text", "text": "We are open 10am-6pm."}],
        },
    ],
    "model": "claude-sonnet-4-6",
    "usage": {"input_tokens": 100, "output_tokens": 50},
}

SAMPLE_LOG_ENTRY_2 = {
    "customer_id": "CUS-001",
    "business_id": "test_biz",
    "timestamp": "2026-03-21T10:00:00+00:00",
    "system_prompt": "You are a helpful agent.",
    "turns": [
        {"role": "user", "content": "Book me an appointment."},
        {
            "role": "assistant",
            "content": [
                {"type": "tool_use", "id": "t1", "name": "lookup_appointments", "input": {}},
            ],
        },
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "No slots."}],
        },
        {
            "role": "assistant",
            "content": [{"type": "text", "text": "Sorry, no slots available."}],
        },
    ],
    "model": "claude-sonnet-4-6",
    "usage": {"input_tokens": 200, "output_tokens": 80},
}


def _write_logs(tmp_dir: Path):
    biz_dir = tmp_dir / "test_biz"
    biz_dir.mkdir(parents=True)
    log_file = biz_dir / "CUS-001.jsonl"
    with open(log_file, "w") as f:
        f.write(json.dumps(SAMPLE_LOG_ENTRY) + "\n")
        f.write(json.dumps(SAMPLE_LOG_ENTRY_2) + "\n")


def test_list_customers_with_logs():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_logs(tmp_path)
        with patch("agent.log_reader.LOGS_DIR", tmp_path):
            result = list_customers_with_logs("test_biz")

    assert len(result) == 1
    assert result[0]["customer_id"] == "CUS-001"
    assert result[0]["total_interactions"] == 2
    assert result[0]["total_tokens"]["input"] == 300
    assert result[0]["total_tokens"]["output"] == 130


def test_list_log_entries():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_logs(tmp_path)
        with patch("agent.log_reader.LOGS_DIR", tmp_path):
            result = list_log_entries("test_biz", "CUS-001")

    assert len(result) == 2
    # Sorted by timestamp descending
    assert result[0]["timestamp"] == "2026-03-21T10:00:00+00:00"
    assert result[0]["customer_message"] == "Book me an appointment."
    assert result[0]["draft_reply"] == "Sorry, no slots available."
    assert result[0]["turns_count"] == 4

    assert result[1]["customer_message"] == "What are your hours?"


def test_get_log_entry():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_logs(tmp_path)
        with patch("agent.log_reader.LOGS_DIR", tmp_path):
            entry = get_log_entry("test_biz", "CUS-001", 1)

    assert entry is not None
    assert entry["index"] == 1
    assert entry["timestamp"] == "2026-03-21T10:00:00+00:00"
    # Multi-turn entry should have 2 LLM calls (tool use + final)
    assert len(entry["llm_calls"]) == 2
    assert entry["llm_calls"][0]["call_index"] == 0
    assert entry["llm_calls"][1]["call_index"] == 1


def test_get_log_entry_out_of_range():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        _write_logs(tmp_path)
        with patch("agent.log_reader.LOGS_DIR", tmp_path):
            entry = get_log_entry("test_biz", "CUS-001", 99)

    assert entry is None


def test_list_customers_empty_business():
    with tempfile.TemporaryDirectory() as tmp:
        with patch("agent.log_reader.LOGS_DIR", Path(tmp)):
            result = list_customers_with_logs("nonexistent")

    assert result == []
