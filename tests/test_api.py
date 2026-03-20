from unittest.mock import patch

from fastapi.testclient import TestClient

from agent.api import app

client = TestClient(app)


def test_chat_invalid_business():
    resp = client.post("/chat", json={
        "business_id": "nonexistent",
        "customer_id": "alice@example.com",
        "message": "hello",
    })
    assert resp.status_code == 404


@patch("agent.api.run_agent_loop")
def test_chat_success(mock_loop):
    mock_loop.return_value = "Hello! How can I help you today?"

    resp = client.post("/chat", json={
        "business_id": "acme_retail",
        "customer_id": "alice@example.com",
        "message": "Hi there",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["customer_id"] == "alice@example.com"
    assert data["reply"] == "Hello! How can I help you today?"
    mock_loop.assert_called_once()


@patch("agent.api.run_agent_loop")
def test_chat_session_continuity(mock_loop):
    mock_loop.return_value = "First reply"
    resp1 = client.post("/chat", json={
        "business_id": "acme_retail",
        "customer_id": "bob@example.com",
        "message": "First message",
    })
    assert resp1.json()["customer_id"] == "bob@example.com"

    mock_loop.return_value = "Second reply"
    resp2 = client.post("/chat", json={
        "business_id": "acme_retail",
        "customer_id": "bob@example.com",
        "message": "Second message",
    })
    assert resp2.json()["customer_id"] == "bob@example.com"
    assert resp2.json()["reply"] == "Second reply"
