import json
from datetime import datetime, timezone
from pathlib import Path

LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs" / "llm"


def log_interaction(
    customer_id: str,
    business_id: str,
    turns: list[dict],
    model: str,
    usage: dict,
    system_prompt: str,
) -> Path:
    """Append an agent loop invocation as a JSONL line.

    Logs to logs/llm/{business_id}/{customer_id}.jsonl.
    """
    business_dir = LOGS_DIR / _safe(business_id)
    business_dir.mkdir(parents=True, exist_ok=True)

    log_path = business_dir / f"{_safe(customer_id)}.jsonl"

    log_entry = {
        "customer_id": customer_id,
        "business_id": business_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "system_prompt": system_prompt,
        "turns": _make_serializable(turns),
        "model": model,
        "usage": usage,
    }

    with open(log_path, "a") as f:
        f.write(json.dumps(log_entry, default=str) + "\n")

    return log_path


def _safe(name: str) -> str:
    """Sanitize a name for use as a file/directory name."""
    return name.replace("/", "_").replace("\\", "_").replace("..", "_")


def _make_serializable(turns: list[dict]) -> list[dict]:
    """Convert Anthropic content blocks to plain dicts for JSON serialization."""
    result = []
    for turn in turns:
        entry = {"role": turn["role"]}
        content = turn["content"]
        if isinstance(content, str):
            entry["content"] = content
        elif isinstance(content, list):
            entry["content"] = [_block_to_dict(b) if hasattr(b, "type") else b for b in content]
        else:
            entry["content"] = str(content)
        result.append(entry)
    return result


def _block_to_dict(block) -> dict:
    if block.type == "text":
        return {"type": "text", "text": block.text}
    elif block.type == "tool_use":
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": block.input,
        }
    return {"type": block.type, "data": str(block)}
