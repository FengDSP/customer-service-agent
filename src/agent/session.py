import uuid


_sessions: dict[str, list[dict]] = {}


def get_or_create_session(session_id: str | None) -> tuple[str, list[dict]]:
    """Return (session_id, history). Creates a new session if needed."""
    if not session_id:
        session_id = str(uuid.uuid4())
    if session_id not in _sessions:
        _sessions[session_id] = []
    return session_id, _sessions[session_id]
