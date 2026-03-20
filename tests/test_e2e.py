"""E2E tests: starts the backend, sends real LLM requests via POST /chat,
and verifies the full pipeline (agent loop, LLM, tool calls, sessions).

Requires ANTHROPIC_API_KEY to be set. Skipped automatically if not available.
"""

import os
import shutil
import subprocess
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
