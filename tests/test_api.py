from unittest.mock import patch

from fastapi.testclient import TestClient

from agent.api import app

client = TestClient(app)

MOCK_RESULT = {
    "draft_reply": "Hello! How can I help you today?",
    "internal_note": "",
    "confidence": "high",
    "needs_human_review": False,
    "suggested_actions": [],
}


def test_chat_invalid_business():
    resp = client.post(
        "/chat",
        json={
            "business_id": "nonexistent",
            "customer_id": "alice@example.com",
            "message": "hello",
        },
    )
    assert resp.status_code == 404


@patch("agent.api.run_agent_loop")
def test_chat_success(mock_loop):
    mock_loop.return_value = MOCK_RESULT

    resp = client.post(
        "/chat",
        json={
            "business_id": "acme_retail",
            "customer_id": "alice@example.com",
            "message": "Hi there",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["customer_id"] == "alice@example.com"
    assert data["reply"] == "Hello! How can I help you today?"
    assert data["confidence"] == "high"
    assert data["needs_human_review"] is False
    mock_loop.assert_called_once()


@patch("agent.api.run_agent_loop")
def test_chat_session_continuity(mock_loop):
    mock_loop.return_value = {
        "draft_reply": "First reply",
        "internal_note": "",
        "confidence": "high",
        "needs_human_review": False,
        "suggested_actions": [],
    }
    resp1 = client.post(
        "/chat",
        json={
            "business_id": "acme_retail",
            "customer_id": "continuity-test@example.com",
            "message": "First message",
        },
    )
    assert resp1.json()["customer_id"] == "continuity-test@example.com"

    mock_loop.return_value = {
        "draft_reply": "Second reply",
        "internal_note": "follow-up",
        "confidence": "medium",
        "needs_human_review": True,
        "suggested_actions": ["escalate"],
    }
    resp2 = client.post(
        "/chat",
        json={
            "business_id": "acme_retail",
            "customer_id": "continuity-test@example.com",
            "message": "Second message",
        },
    )
    data2 = resp2.json()
    assert data2["customer_id"] == "continuity-test@example.com"
    assert data2["reply"] == "Second reply"
    assert data2["internal_note"] == "follow-up"
    assert data2["needs_human_review"] is True
    assert data2["suggested_actions"] == ["escalate"]
