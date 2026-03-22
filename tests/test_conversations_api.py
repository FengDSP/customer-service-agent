from unittest.mock import patch

from fastapi.testclient import TestClient

from agent.api import _sse_subscribers, app
from agent.session import SESSIONS_DIR, _cache

client = TestClient(app)

BIZ = "beauty_lab"
CUST = "test-cs-worker-cust"


def _cleanup():
    _cache.clear()
    _sse_subscribers.clear()
    path = SESSIONS_DIR / BIZ / f"{CUST}.jsonl"
    if path.exists():
        path.unlink()


def setup_function():
    _cleanup()


def teardown_function():
    _cleanup()


def test_post_message():
    resp = client.post(
        "/messages",
        json={"business_id": BIZ, "customer_id": CUST, "message": "hello"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    # Verify message was recorded in history
    resp = client.get(f"/history/{BIZ}/{CUST}")
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 1
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "hello"


def test_post_message_invalid_business():
    resp = client.post(
        "/messages",
        json={"business_id": "nonexistent", "customer_id": CUST, "message": "hello"},
    )
    assert resp.status_code == 404


def test_pending_empty():
    resp = client.get(f"/conversations/{BIZ}/pending")
    assert resp.status_code == 200
    data = resp.json()
    # Should not include our test customer (no messages yet)
    cust_ids = [c["customer_id"] for c in data]
    assert CUST not in cust_ids


def test_pending_with_unreplied():
    # Send a customer message
    client.post(
        "/messages",
        json={"business_id": BIZ, "customer_id": CUST, "message": "need help"},
    )

    resp = client.get(f"/conversations/{BIZ}/pending")
    assert resp.status_code == 200
    data = resp.json()
    found = [c for c in data if c["customer_id"] == CUST]
    assert len(found) == 1
    assert found[0]["has_unreplied"] is True
    assert "need help" in found[0]["last_message"]


def test_pending_invalid_business():
    resp = client.get("/conversations/nonexistent/pending")
    assert resp.status_code == 404


def test_context():
    resp = client.get(f"/conversations/{BIZ}/CUS-001/context")
    assert resp.status_code == 200
    data = resp.json()
    # beauty_lab has cs_view_sources: [customers, appointments]
    assert "customers" in data
    assert "columns" in data["customers"]
    assert "rows" in data["customers"]
    # CUS-001 should have a row in customers
    assert len(data["customers"]["rows"]) >= 1


def test_context_no_match():
    resp = client.get(f"/conversations/{BIZ}/NONEXISTENT/context")
    assert resp.status_code == 200
    data = resp.json()
    # Should return empty rows
    assert data["customers"]["rows"] == []


def test_send_reply():
    # First send a customer message
    client.post(
        "/messages",
        json={"business_id": BIZ, "customer_id": CUST, "message": "hello"},
    )

    # Then send a reply
    resp = client.post(
        f"/conversations/{BIZ}/{CUST}/send",
        json={"reply": "Hi! How can I help?"},
    )
    assert resp.status_code == 200

    # Verify both messages in history
    resp = client.get(f"/history/{BIZ}/{CUST}")
    history = resp.json()
    assert len(history) == 2
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi! How can I help?"


def test_send_reply_invalid_business():
    resp = client.post(
        "/conversations/nonexistent/{CUST}/send",
        json={"reply": "test"},
    )
    assert resp.status_code == 404


@patch("agent.api.run_agent_loop")
def test_generate_draft(mock_loop):
    mock_loop.return_value = {
        "draft_reply": "hey, how can i help?",
        "internal_note": "",
        "confidence": "high",
        "needs_human_review": False,
        "suggested_actions": [],
    }

    # Send a customer message first
    client.post(
        "/messages",
        json={"business_id": BIZ, "customer_id": CUST, "message": "hi there"},
    )

    resp = client.post(f"/conversations/{BIZ}/{CUST}/draft")
    assert resp.status_code == 200
    data = resp.json()
    assert data["reply"] == "hey, how can i help?"
    assert data["confidence"] == "high"
    mock_loop.assert_called_once()
    # Verify draft_only=True was passed
    call_kwargs = mock_loop.call_args
    assert call_kwargs.kwargs.get("draft_only") is True or call_kwargs[1].get("draft_only") is True


def test_generate_draft_no_unreplied():
    # Send a message and reply
    client.post(
        "/messages",
        json={"business_id": BIZ, "customer_id": CUST, "message": "hello"},
    )
    client.post(
        f"/conversations/{BIZ}/{CUST}/send",
        json={"reply": "hi"},
    )

    # Now try to generate draft — should fail, no unreplied
    resp = client.post(f"/conversations/{BIZ}/{CUST}/draft")
    assert resp.status_code == 400


def test_generate_draft_no_messages():
    resp = client.post(f"/conversations/{BIZ}/{CUST}/draft")
    assert resp.status_code == 400


def test_sse_subscriber_notified_on_message():
    """Test that POST /messages pushes events to SSE subscribers."""
    import asyncio

    queue = asyncio.Queue()
    _sse_subscribers.setdefault(BIZ, []).append(queue)

    try:
        client.post(
            "/messages",
            json={"business_id": BIZ, "customer_id": CUST, "message": "sse test"},
        )

        assert not queue.empty()
        event = queue.get_nowait()
        assert event["event"] == "message"
        assert event["data"]["customer_id"] == CUST
        assert event["data"]["message"] == "sse test"
    finally:
        _sse_subscribers[BIZ].remove(queue)
        if not _sse_subscribers[BIZ]:
            del _sse_subscribers[BIZ]


def test_sse_events_invalid_business():
    resp = client.get("/conversations/nonexistent/events")
    assert resp.status_code == 404
