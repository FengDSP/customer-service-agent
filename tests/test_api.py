from unittest.mock import patch

from fastapi.testclient import TestClient

from agent.api import app

client = TestClient(app)


def test_chat_invalid_business():
    resp = client.post("/chat", json={
        "business_id": "nonexistent",
        "message": "hello",
    })
    assert resp.status_code == 404


@patch("agent.api.run_agent_loop")
def test_chat_success(mock_loop):
    mock_loop.return_value = "Hello! How can I help you today?"

    resp = client.post("/chat", json={
        "business_id": "acme_retail",
        "message": "Hi there",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert data["reply"] == "Hello! How can I help you today?"
    mock_loop.assert_called_once()


@patch("agent.api.run_agent_loop")
def test_chat_session_continuity(mock_loop):
    mock_loop.return_value = "First reply"
    resp1 = client.post("/chat", json={
        "business_id": "acme_retail",
        "message": "First message",
    })
    session_id = resp1.json()["session_id"]

    mock_loop.return_value = "Second reply"
    resp2 = client.post("/chat", json={
        "session_id": session_id,
        "business_id": "acme_retail",
        "message": "Second message",
    })
    assert resp2.json()["session_id"] == session_id
    assert resp2.json()["reply"] == "Second reply"
