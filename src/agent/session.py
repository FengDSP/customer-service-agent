_sessions: dict[str, list[dict]] = {}


def get_or_create_session(customer_id: str) -> list[dict]:
    """Return conversation history for a customer. Creates a new session if needed."""
    if customer_id not in _sessions:
        _sessions[customer_id] = []
    return _sessions[customer_id]
