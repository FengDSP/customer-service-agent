"""Read and parse LLM call logs from JSONL files."""

import json
from pathlib import Path

LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs" / "llm"


def list_customers_with_logs(business_id: str) -> list[dict]:
    """List customers with log files for a business, sorted by last interaction."""
    business_dir = LOGS_DIR / business_id
    if not business_dir.is_dir():
        return []

    customers = []
    for jsonl_file in business_dir.glob("*.jsonl"):
        customer_id = jsonl_file.stem
        entries = _read_jsonl(jsonl_file)
        if not entries:
            continue

        total_input = sum(e.get("usage", {}).get("input_tokens", 0) for e in entries)
        total_output = sum(e.get("usage", {}).get("output_tokens", 0) for e in entries)
        last_ts = max(e.get("timestamp", "") for e in entries)

        customers.append({
            "customer_id": customer_id,
            "last_interaction": last_ts,
            "total_interactions": len(entries),
            "total_tokens": {"input": total_input, "output": total_output},
        })

    customers.sort(key=lambda c: c["last_interaction"], reverse=True)
    return customers


def list_log_entries(business_id: str, customer_id: str) -> list[dict]:
    """List all log entries for a customer with summary fields."""
    entries = _read_customer_logs(business_id, customer_id)
    summaries = []
    for i, entry in enumerate(entries):
        turns = entry.get("turns", [])
        customer_message = _extract_customer_message(turns)
        draft_reply = _extract_draft_reply(turns)

        summaries.append({
            "index": i,
            "timestamp": entry.get("timestamp", ""),
            "customer_message": customer_message[:200] if customer_message else "",
            "draft_reply": draft_reply[:200] if draft_reply else "",
            "model": entry.get("model", ""),
            "confidence": _extract_confidence(draft_reply),
            "usage": entry.get("usage", {}),
            "turns_count": len(turns),
        })

    summaries.sort(key=lambda s: s["timestamp"], reverse=True)
    return summaries


def get_log_entry(business_id: str, customer_id: str, log_index: int) -> dict | None:
    """Get a full log entry by index."""
    entries = _read_customer_logs(business_id, customer_id)
    if 0 <= log_index < len(entries):
        entry = entries[log_index]
        entry["index"] = log_index
        entry["llm_calls"] = _extract_llm_calls(entry)
        return entry
    return None


def _extract_llm_calls(entry: dict) -> list[dict]:
    """Extract individual LLM call boundaries from a multi-turn log entry.

    Each LLM call consists of the messages sent up to that point and the assistant response.
    In a tool-use loop, there are multiple LLM calls per entry.
    """
    turns = entry.get("turns", [])
    system_prompt = entry.get("system_prompt", "")
    model = entry.get("model", "")

    calls = []
    messages_so_far = []
    call_index = 0

    for turn in turns:
        role = turn.get("role", "")
        if role == "assistant":
            # This is an LLM response — marks the end of an LLM call
            calls.append({
                "call_index": call_index,
                "system": system_prompt,
                "messages": list(messages_so_far),  # messages sent to get this response
                "response": turn,
                "model": model,
            })
            messages_so_far.append(turn)
            call_index += 1
        else:
            messages_so_far.append(turn)

    return calls


def _read_customer_logs(business_id: str, customer_id: str) -> list[dict]:
    """Read all log entries for a customer."""
    log_path = LOGS_DIR / business_id / f"{customer_id}.jsonl"
    if not log_path.is_file():
        return []
    return _read_jsonl(log_path)


def _read_jsonl(path: Path) -> list[dict]:
    """Read a JSONL file and return a list of parsed entries."""
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries


def _extract_customer_message(turns: list[dict]) -> str:
    """Extract the first user message from turns."""
    for turn in turns:
        if turn.get("role") == "user":
            content = turn.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        return block.get("text", "")
    return ""


def _extract_draft_reply(turns: list[dict]) -> str:
    """Extract the last assistant text response from turns."""
    for turn in reversed(turns):
        if turn.get("role") == "assistant":
            content = turn.get("content", "")
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                texts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        texts.append(block.get("text", ""))
                return "\n".join(texts)
    return ""


def _extract_confidence(draft_reply: str) -> str:
    """Try to extract confidence from JSON draft reply."""
    try:
        data = json.loads(draft_reply)
        return data.get("confidence", "unknown")
    except (json.JSONDecodeError, TypeError):
        return "unknown"
