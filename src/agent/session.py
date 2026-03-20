import json
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SESSIONS_DIR = PROJECT_ROOT / "data" / "sessions"

_cache: dict[str, list[dict]] = {}


def get_or_create_session(business_id: str, customer_id: str) -> list[dict]:
    """Return conversation history for a customer, loading from disk if available."""
    key = f"{business_id}/{customer_id}"
    if key not in _cache:
        _cache[key] = _load_history(business_id, customer_id)
    return _cache[key]


def append_message(business_id: str, customer_id: str, message: dict) -> None:
    """Append a message (with timestamp) to the session history file."""
    if "timestamp" not in message:
        message["timestamp"] = datetime.now().isoformat()
    path = _session_path(business_id, customer_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(message) + "\n")


def _load_history(business_id: str, customer_id: str) -> list[dict]:
    path = _session_path(business_id, customer_id)
    if not path.exists():
        return []
    history = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                history.append(json.loads(line))
    return history


def _session_path(business_id: str, customer_id: str) -> Path:
    safe_biz = business_id.replace("/", "_").replace("\\", "_")
    safe_cust = customer_id.replace("/", "_").replace("\\", "_")
    return SESSIONS_DIR / safe_biz / f"{safe_cust}.jsonl"
