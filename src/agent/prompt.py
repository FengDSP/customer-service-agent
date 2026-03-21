"""Build structured user prompts for the LLM with metadata and conversation context."""

from datetime import datetime

from agent.config import BusinessConfig

HISTORY_WINDOW = 20

RESPONSE_FORMAT = """\
{
  "draft_reply": "your reply message to the customer",
  "internal_note": "optional note for the human reviewer about your reasoning or flagged issues",
  "confidence": "high | medium | low",
  "needs_human_review": true or false,
  "suggested_actions": ["optional list of follow-up actions, e.g. send refund, escalate"]
}"""


def build_user_prompt(
    message: str,
    history: list[dict],
    config: BusinessConfig,
    customer_id: str,
) -> str:
    """Build a structured user prompt with metadata and conversation context."""
    now = datetime.now()
    recent, summary = _split_history(history)
    total_messages = len(history)
    session_start = _get_session_start(history)

    parts = [
        "Draft the customer service reply message. "
        "A human customer service agent will audit your draft before sending.",
        "",
        "<customer_message>",
        message,
        "</customer_message>",
    ]

    if recent:
        parts.append("")
        parts.append(
            f'<conversation_history count="{len(recent)}" showing="last {HISTORY_WINDOW}">'
        )
        for msg in recent:
            ts = msg.get("timestamp", "")
            ts_str = f"[{ts}] " if ts else ""
            sender = "customer" if msg["role"] == "user" else "agent"
            parts.append(f"{ts_str}{sender}: {msg['content']}")
        parts.append("</conversation_history>")

    if summary:
        parts.append("")
        parts.append("<older_conversation_summary>")
        parts.append(summary)
        parts.append("</older_conversation_summary>")

    parts.append("")
    parts.append("<metadata>")
    parts.append(f"  <customer_id>{customer_id}</customer_id>")
    parts.append(f"  <business_id>{config.business_id}</business_id>")
    parts.append(f"  <business_name>{config.name}</business_name>")
    parts.append(f"  <current_time>{now.isoformat()}</current_time>")
    parts.append(f"  <total_messages>{total_messages}</total_messages>")
    if session_start:
        parts.append(f"  <session_start>{session_start}</session_start>")
    parts.append("</metadata>")

    parts.append("")
    parts.append("Respond with a JSON object in this exact format:")
    parts.append(RESPONSE_FORMAT)

    return "\n".join(parts)


def _split_history(history: list[dict]) -> tuple[list[dict], str]:
    """Split history into recent messages and a summary of older ones."""
    if len(history) <= HISTORY_WINDOW:
        return history, ""

    older = history[:-HISTORY_WINDOW]
    recent = history[-HISTORY_WINDOW:]

    summary_lines = []
    for msg in older:
        sender = "customer" if msg["role"] == "user" else "agent"
        text = msg["content"]
        if len(text) > 100:
            text = text[:100] + "..."
        summary_lines.append(f"- {sender}: {text}")

    summary = f"{len(older)} earlier messages:\n" + "\n".join(summary_lines)
    return recent, summary


def _get_session_start(history: list[dict]) -> str:
    """Get the timestamp of the first message, if available."""
    if history and "timestamp" in history[0]:
        return history[0]["timestamp"]
    return ""
