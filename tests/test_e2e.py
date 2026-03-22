"""E2E tests: starts the backend, sends real LLM requests via POST /chat,
and verifies the full pipeline (agent loop, LLM, tool calls, sessions).

Requires ANTHROPIC_API_KEY to be set. Skipped automatically if not available.
"""

import json
import os
import shutil
import subprocess
import threading
import time
from pathlib import Path

import httpx
import pytest

BASE_URL = "http://127.0.0.1:8000"
BUSINESS_ID = "acme_retail"
CUSTOMER_ID = "e2e-test@example.com"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs" / "llm"
SESSIONS_DIR = PROJECT_ROOT / "data" / "sessions"

pytestmark = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)


@pytest.fixture(scope="module")
def server():
    """Start the backend server for the duration of the test module."""
    # Clean test data
    for d in [LOGS_DIR, SESSIONS_DIR / BUSINESS_ID]:
        if d.exists():
            shutil.rmtree(d)

    proc = subprocess.Popen(
        ["uvicorn", "agent.api:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=PROJECT_ROOT,
    )

    for _ in range(40):
        try:
            httpx.get(f"{BASE_URL}/docs", timeout=1.0)
            break
        except (httpx.ConnectError, httpx.TimeoutException):
            time.sleep(0.5)
    else:
        proc.kill()
        pytest.fail("Server did not start in time")

    yield proc

    proc.terminate()
    proc.wait(timeout=5)


def _chat(message: str) -> dict:
    resp = httpx.post(
        f"{BASE_URL}/chat",
        json={"business_id": BUSINESS_ID, "customer_id": CUSTOMER_ID, "message": message},
        timeout=60.0,
    )
    assert resp.status_code == 200, f"Unexpected status {resp.status_code}: {resp.text}"
    return resp.json()


def test_greeting(server):
    data = _chat("Hello, I need some help.")
    assert data["customer_id"] == CUSTOMER_ID
    assert len(data["reply"]) > 0
    assert "confidence" in data


def test_order_lookup_tool_call(server):
    data = _chat("What is the status of order ORD-1002?")
    assert len(data["reply"]) > 0
    assert "ship" in data["reply"].lower() or len(data["reply"]) > 20


def test_session_continuity(server):
    data = _chat("And what about order ORD-1003?")
    assert data["customer_id"] == CUSTOMER_ID
    assert len(data["reply"]) > 0


def test_llm_logs_created(server):
    log_files = list(LOGS_DIR.rglob("*.jsonl"))
    assert len(log_files) >= 1, f"Expected log files, found {len(log_files)}"


# --- CS Worker flow e2e ---

CS_BIZ = "beauty_lab"
CS_CUST = "e2e-cs-worker"


def test_cs_worker_full_flow(server):
    """E2e: post customer message → appears in pending → generate draft → send reply → verify."""

    # 1. Post a customer message (simulates CLI --as-customer)
    resp = httpx.post(
        f"{BASE_URL}/messages",
        json={
            "business_id": CS_BIZ,
            "customer_id": CS_CUST,
            "message": "When is my next appointment?",
        },
        timeout=10.0,
    )
    assert resp.status_code == 200

    # 2. Verify customer appears in pending list with unreplied flag
    resp = httpx.get(f"{BASE_URL}/conversations/{CS_BIZ}/pending", timeout=10.0)
    assert resp.status_code == 200
    pending = resp.json()
    found = [c for c in pending if c["customer_id"] == CS_CUST]
    cust_ids = [c["customer_id"] for c in pending]
    assert len(found) == 1, f"Expected {CS_CUST} in pending, got {cust_ids}"
    assert found[0]["has_unreplied"] is True

    # 3. Check customer context returns data
    resp = httpx.get(f"{BASE_URL}/conversations/{CS_BIZ}/{CS_CUST}/context", timeout=10.0)
    assert resp.status_code == 200

    # 4. Generate a draft reply (hits real LLM)
    resp = httpx.post(
        f"{BASE_URL}/conversations/{CS_BIZ}/{CS_CUST}/draft",
        timeout=60.0,
    )
    assert resp.status_code == 200
    draft = resp.json()
    assert len(draft["reply"]) > 0
    assert "confidence" in draft

    # 5. Send the approved reply
    resp = httpx.post(
        f"{BASE_URL}/conversations/{CS_BIZ}/{CS_CUST}/send",
        json={"reply": draft["reply"]},
        timeout=10.0,
    )
    assert resp.status_code == 200

    # 6. Verify reply is recorded in session history
    resp = httpx.get(f"{BASE_URL}/history/{CS_BIZ}/{CS_CUST}", timeout=10.0)
    assert resp.status_code == 200
    history = resp.json()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == draft["reply"]

    # 7. Verify no longer unreplied in pending
    resp = httpx.get(f"{BASE_URL}/conversations/{CS_BIZ}/pending", timeout=10.0)
    found = [c for c in resp.json() if c["customer_id"] == CS_CUST]
    assert len(found) == 1
    assert found[0]["has_unreplied"] is False


# --- SSE async flow e2e ---

SSE_CUST = "e2e-sse-test"


def test_sse_async_flow(server):
    """E2e: connect SSE, post a customer message, verify event arrives via SSE."""
    received_events = []
    stop_event = threading.Event()

    def sse_listener():
        """Listen for SSE events in a background thread."""
        try:
            with httpx.stream(
                "GET",
                f"{BASE_URL}/conversations/{CS_BIZ}/events",
                timeout=30.0,
            ) as resp:
                for line in resp.iter_lines():
                    if stop_event.is_set():
                        break
                    if line.startswith("data: "):
                        data = json.loads(line[6:])
                        received_events.append(data)
                        if data.get("customer_id") == SSE_CUST:
                            break
        except (httpx.ReadTimeout, httpx.RemoteProtocolError):
            pass

    # Start SSE listener in background
    listener_thread = threading.Thread(target=sse_listener, daemon=True)
    listener_thread.start()

    # Give SSE connection time to establish
    time.sleep(1.0)

    # Post a customer message — should trigger SSE event
    resp = httpx.post(
        f"{BASE_URL}/messages",
        json={
            "business_id": CS_BIZ,
            "customer_id": SSE_CUST,
            "message": "SSE test message",
        },
        timeout=10.0,
    )
    assert resp.status_code == 200

    # Wait for SSE event to arrive
    listener_thread.join(timeout=10.0)
    stop_event.set()

    # Verify we received the SSE event
    matching = [e for e in received_events if e.get("customer_id") == SSE_CUST]
    assert len(matching) >= 1, f"Expected SSE event for {SSE_CUST}, got {received_events}"
    assert matching[0]["message"] == "SSE test message"
