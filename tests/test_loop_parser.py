import json

from agent.loop import _parse_response


def test_parse_valid_json():
    data = {
        "draft_reply": "Hello!",
        "internal_note": "greeting",
        "confidence": "high",
        "needs_human_review": False,
        "suggested_actions": ["follow up"],
    }
    result = _parse_response(json.dumps(data))
    assert result["draft_reply"] == "Hello!"
    assert result["confidence"] == "high"
    assert result["suggested_actions"] == ["follow up"]


def test_parse_json_with_code_fences():
    text = '```json\n{"draft_reply": "Hi!", "confidence": "medium"}\n```'
    result = _parse_response(text)
    assert result["draft_reply"] == "Hi!"
    assert result["confidence"] == "medium"


def test_parse_fallback_plain_text():
    result = _parse_response("Just a plain text reply")
    assert result["draft_reply"] == "Just a plain text reply"
    assert result["confidence"] == "low"
    assert result["needs_human_review"] is True
    assert "did not return valid JSON" in result["internal_note"]


def test_parse_missing_fields_get_defaults():
    result = _parse_response('{"draft_reply": "Hi"}')
    assert result["draft_reply"] == "Hi"
    assert result["internal_note"] == ""
    assert result["confidence"] == "medium"
    assert result["needs_human_review"] is False
    assert result["suggested_actions"] == []
