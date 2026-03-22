"""E2e test for CLI customer mode: message → SSE reply flow.

Tests the full flow:
1. Customer sends message via POST /messages
2. Verify SSE event is queued for connected clients
3. CS agent sends reply via POST .../send
4. Verify reply SSE event is queued
5. Verify conversation history has both messages
"""

import asyncio

from fastapi.testclient import TestClient

from agent.api import _sse_subscribers, app
from agent.session import SESSIONS_DIR, _cache

client = TestClient(app)

BIZ = "beauty_lab"
CUST = "test-cli-cust-mode"


def _cleanup():
    _cache.clear()
    for cust in [CUST, "test-cli-other-cust"]:
        path = SESSIONS_DIR / BIZ / f"{cust}.jsonl"
        if path.exists():
            path.unlink()
    _sse_subscribers.pop(BIZ, None)


def setup_function():
    _cleanup()


def teardown_function():
    _cleanup()


def _subscribe(business_id: str) -> asyncio.Queue:
    """Register a queue to receive SSE events for a business (simulates SSE client)."""
    q: asyncio.Queue = asyncio.Queue()
    _sse_subscribers.setdefault(business_id, []).append(q)
    return q


def test_message_and_reply_full_flow():
    """Full flow: customer sends message, CS agent replies, events published."""
    q = _subscribe(BIZ)

    # Step 1: Customer sends a message
    resp = client.post(
        "/messages",
        json={
            "business_id": BIZ,
            "customer_id": CUST,
            "message": "I need help with my appointment",
        },
    )
    assert resp.status_code == 200

    # Verify message event was published
    event = q.get_nowait()
    assert event["event"] == "message"
    assert event["data"]["customer_id"] == CUST
    assert event["data"]["message"] == "I need help with my appointment"
    assert "timestamp" in event["data"]

    # Step 2: CS agent sends a reply
    resp = client.post(
        f"/conversations/{BIZ}/{CUST}/send",
        json={"reply": "Sure, let me look up your appointment."},
    )
    assert resp.status_code == 200

    # Verify reply event was published
    event = q.get_nowait()
    assert event["event"] == "reply"
    assert event["data"]["customer_id"] == CUST
    assert event["data"]["reply"] == "Sure, let me look up your appointment."
    assert "timestamp" in event["data"]

    # Step 3: Verify conversation history
    resp = client.get(f"/history/{BIZ}/{CUST}")
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "I need help with my appointment"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Sure, let me look up your appointment."

    # Queue should be empty now
    assert q.empty()


def test_events_broadcast_to_multiple_subscribers():
    """Multiple SSE clients all receive the same events."""
    q1 = _subscribe(BIZ)
    q2 = _subscribe(BIZ)

    client.post(
        "/messages",
        json={"business_id": BIZ, "customer_id": CUST, "message": "hello"},
    )

    e1 = q1.get_nowait()
    e2 = q2.get_nowait()
    assert e1 == e2
    assert e1["event"] == "message"
    assert e1["data"]["customer_id"] == CUST


def test_events_include_all_customers():
    """Events for different customers all arrive on the same business stream."""
    other_cust = "test-cli-other-cust"
    q = _subscribe(BIZ)

    client.post(
        "/messages",
        json={"business_id": BIZ, "customer_id": CUST, "message": "msg from cust 1"},
    )
    client.post(
        "/messages",
        json={"business_id": BIZ, "customer_id": other_cust, "message": "msg from cust 2"},
    )

    events = [q.get_nowait(), q.get_nowait()]
    cust_ids = [e["data"]["customer_id"] for e in events]
    assert CUST in cust_ids
    assert other_cust in cust_ids


def test_no_events_without_subscriber():
    """Publishing without subscribers doesn't error."""
    resp = client.post(
        "/messages",
        json={"business_id": BIZ, "customer_id": CUST, "message": "no one listening"},
    )
    assert resp.status_code == 200


def test_sse_endpoint_invalid_business():
    """SSE endpoint returns 404 for unknown business."""
    resp = client.get("/conversations/nonexistent/events")
    assert resp.status_code == 404
