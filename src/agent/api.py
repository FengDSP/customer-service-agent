import asyncio
import json
import logging
from pathlib import Path

import anthropic
import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.responses import StreamingResponse

from agent.config import CONFIGS_DIR, load_business_config
from agent.log_reader import get_log_entry, list_customers_with_logs, list_log_entries
from agent.loop import run_agent_loop
from agent.session import SESSIONS_DIR, append_message, get_or_create_session

load_dotenv()

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

app = FastAPI(title="Customer Service Agent")

# Allow Next.js dev server to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- SSE pub/sub ---
# {business_id: [asyncio.Queue, ...]}
_sse_subscribers: dict[str, list[asyncio.Queue]] = {}
_shutdown_event = asyncio.Event()


@app.on_event("shutdown")
async def _on_shutdown():
    """Signal all SSE connections to close so uvicorn can exit promptly."""
    _shutdown_event.set()
    # Push a sentinel to unblock any queues waiting in asyncio.wait_for
    for queues in _sse_subscribers.values():
        for q in queues:
            await q.put(None)


async def _publish_event(business_id: str, event_type: str, data: dict):
    """Push an SSE event to all connected clients for a business."""
    for q in _sse_subscribers.get(business_id, []):
        await q.put({"event": event_type, "data": data})


class ChatRequest(BaseModel):
    business_id: str
    customer_id: str
    message: str


class ChatResponse(BaseModel):
    customer_id: str
    reply: str
    internal_note: str = ""
    confidence: str = "medium"
    needs_human_review: bool = False
    suggested_actions: list[str] = []


class BusinessInfo(BaseModel):
    business_id: str
    name: str


class CustomerInfo(BaseModel):
    customer_id: str
    name: str


class MessageRequest(BaseModel):
    business_id: str
    customer_id: str
    message: str


class SendRequest(BaseModel):
    reply: str


class ConversationSummary(BaseModel):
    customer_id: str
    name: str
    last_message: str
    last_timestamp: str
    has_unreplied: bool


@app.get("/businesses", response_model=list[BusinessInfo])
async def list_businesses():
    results = []
    for path in sorted(CONFIGS_DIR.glob("*.yaml")):
        config = load_business_config(path.stem)
        results.append(BusinessInfo(business_id=config.business_id, name=config.name))
    return results


@app.get("/businesses/{business_id}/customers", response_model=list[CustomerInfo])
async def list_customers(business_id: str):
    try:
        config = load_business_config(business_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Business '{business_id}' not found")

    # Look for a "customers" data source with customer_id and name columns
    for ds in config.data_sources:
        if ds.name == "customers":
            csv_path = PROJECT_ROOT / ds.path
            df = pd.read_csv(csv_path, dtype=str)
            if "customer_id" in df.columns and "name" in df.columns:
                return [
                    CustomerInfo(customer_id=row["customer_id"], name=row["name"])
                    for _, row in df.iterrows()
                ]

    return []


@app.get("/history/{business_id}/{customer_id}")
async def get_history(business_id: str, customer_id: str):
    history = await get_or_create_session(business_id, customer_id)
    return history


@app.post("/messages")
async def post_message(req: MessageRequest):
    """Record a customer message without running the agent loop."""
    try:
        load_business_config(req.business_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Business '{req.business_id}' not found")

    history = await get_or_create_session(req.business_id, req.customer_id)
    msg = {"role": "user", "content": req.message}
    history.append(msg)
    await append_message(req.business_id, req.customer_id, msg)
    await _publish_event(
        req.business_id,
        "message",
        {
            "customer_id": req.customer_id,
            "message": req.message,
            "timestamp": msg.get("timestamp", ""),
        },
    )
    return {"status": "ok"}


@app.get("/conversations/{business_id}/pending", response_model=list[ConversationSummary])
async def list_pending_conversations(business_id: str):
    """List all customers with messages, unreplied first."""
    try:
        config = load_business_config(business_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Business '{business_id}' not found")

    # Build a name lookup from customers CSV if available
    name_lookup: dict[str, str] = {}
    for ds in config.data_sources:
        if ds.name == "customers":
            csv_path = PROJECT_ROOT / ds.path
            if csv_path.exists():
                df = pd.read_csv(csv_path, dtype=str)
                if "customer_id" in df.columns and "name" in df.columns:
                    for _, row in df.iterrows():
                        name_lookup[row["customer_id"]] = row["name"]
            break

    biz_dir = SESSIONS_DIR / business_id
    if not biz_dir.exists():
        return []

    results = []
    for session_file in biz_dir.glob("*.jsonl"):
        customer_id = session_file.stem
        history = await get_or_create_session(business_id, customer_id)
        if not history:
            continue

        last_msg = history[-1]
        has_unreplied = last_msg.get("role") == "user"
        results.append(
            ConversationSummary(
                customer_id=customer_id,
                name=name_lookup.get(customer_id, customer_id),
                last_message=last_msg.get("content", "")[:100],
                last_timestamp=last_msg.get("timestamp", ""),
                has_unreplied=has_unreplied,
            )
        )

    # Sort: unreplied first, then by timestamp descending
    results.sort(key=lambda c: c.last_timestamp, reverse=True)
    results.sort(key=lambda c: not c.has_unreplied)
    return results


@app.get("/conversations/{business_id}/{customer_id}/context")
async def get_customer_context(business_id: str, customer_id: str):
    """Return CSV rows matching this customer from configured cs_view_sources."""
    try:
        config = load_business_config(business_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Business '{business_id}' not found")

    result = {}
    source_map = {ds.name: ds for ds in config.data_sources}

    for source_name in config.cs_view_sources:
        ds = source_map.get(source_name)
        if not ds:
            continue
        csv_path = PROJECT_ROOT / ds.path
        if not csv_path.exists():
            continue
        df = pd.read_csv(csv_path, dtype=str).fillna("")
        if "customer_id" in df.columns:
            df = df[df["customer_id"] == customer_id]
        result[source_name] = {
            "columns": list(df.columns),
            "rows": df.values.tolist(),
        }

    return result


@app.post("/conversations/{business_id}/{customer_id}/draft")
async def generate_draft(business_id: str, customer_id: str):
    """Generate a draft reply for the latest unreplied message.

    Unlike POST /chat, this does NOT append the user message (it's already recorded
    by POST /messages). It runs the agent loop in draft-only mode and returns the
    draft without recording the assistant reply — that happens via POST .../send.
    """
    try:
        config = load_business_config(business_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Business '{business_id}' not found")

    history = await get_or_create_session(business_id, customer_id)
    if not history:
        raise HTTPException(status_code=400, detail="No messages in conversation")

    last_msg = history[-1]
    if last_msg.get("role") != "user":
        raise HTTPException(status_code=400, detail="No unreplied message")

    try:
        result = await run_agent_loop(
            config, history, last_msg["content"], customer_id, draft_only=True
        )
    except Exception as e:
        logger.error("Draft generation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "reply": result["draft_reply"],
        "internal_note": result.get("internal_note", ""),
        "confidence": result.get("confidence", "medium"),
        "needs_human_review": result.get("needs_human_review", False),
        "suggested_actions": result.get("suggested_actions", []),
    }


@app.post("/conversations/{business_id}/{customer_id}/send")
async def send_reply(business_id: str, customer_id: str, req: SendRequest):
    """Record an approved reply in the session."""
    try:
        load_business_config(business_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Business '{business_id}' not found")

    history = await get_or_create_session(business_id, customer_id)
    msg = {"role": "assistant", "content": req.reply}
    history.append(msg)
    await append_message(business_id, customer_id, msg)
    await _publish_event(
        business_id,
        "reply",
        {
            "customer_id": customer_id,
            "reply": req.reply,
            "timestamp": msg.get("timestamp", ""),
        },
    )
    return {"status": "ok"}


@app.get("/conversations/{business_id}/events")
async def conversation_events(business_id: str):
    """SSE endpoint streaming real-time message and reply events for a business."""
    try:
        load_business_config(business_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Business '{business_id}' not found")

    q: asyncio.Queue = asyncio.Queue()
    _sse_subscribers.setdefault(business_id, []).append(q)

    async def event_stream():
        try:
            while not _shutdown_event.is_set():
                try:
                    event = await asyncio.wait_for(q.get(), timeout=30)
                    if event is None:
                        break
                    yield f"event: {event['event']}\ndata: {json.dumps(event['data'])}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            _sse_subscribers[business_id].remove(q)
            if not _sse_subscribers[business_id]:
                del _sse_subscribers[business_id]

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    logger.info("[%s] customer=%s message: %s", req.business_id, req.customer_id, req.message)

    try:
        config = load_business_config(req.business_id)
    except FileNotFoundError:
        logger.warning("Business not found: %s", req.business_id)
        raise HTTPException(status_code=404, detail=f"Business '{req.business_id}' not found")

    history = await get_or_create_session(req.business_id, req.customer_id)
    logger.info(
        "[%s] customer=%s history=%d messages",
        req.business_id,
        req.customer_id,
        len(history),
    )

    try:
        result = await run_agent_loop(config, history, req.message, req.customer_id)
    except Exception as e:
        logger.error(
            "[%s] customer=%s agent loop failed: %s",
            req.business_id,
            req.customer_id,
            e,
        )
        raise HTTPException(status_code=500, detail=str(e))

    logger.info(
        "[%s] customer=%s reply: confidence=%s, needs_review=%s",
        req.business_id,
        req.customer_id,
        result.get("confidence"),
        result.get("needs_human_review"),
    )

    return ChatResponse(
        customer_id=req.customer_id,
        reply=result["draft_reply"],
        internal_note=result.get("internal_note", ""),
        confidence=result.get("confidence", "medium"),
        needs_human_review=result.get("needs_human_review", False),
        suggested_actions=result.get("suggested_actions", []),
    )


# --- Admin endpoints ---


@app.get("/admin/logs/{business_id}/customers")
async def admin_list_customers_with_logs(business_id: str):
    return list_customers_with_logs(business_id)


@app.get("/admin/logs/{business_id}/{customer_id}")
async def admin_list_log_entries(business_id: str, customer_id: str):
    return list_log_entries(business_id, customer_id)


@app.get("/admin/logs/{business_id}/{customer_id}/{log_index}")
async def admin_get_log_entry(business_id: str, customer_id: str, log_index: int):
    entry = get_log_entry(business_id, customer_id, log_index)
    if entry is None:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return entry


class ReplayRequest(BaseModel):
    model: str
    system: str
    messages: list[dict]
    tools: list[dict] = []
    original_response_text: str = ""


@app.post("/admin/replay")
async def admin_replay(req: ReplayRequest):
    client = anthropic.AsyncAnthropic()
    try:
        kwargs = {
            "model": req.model,
            "max_tokens": 2048,
            "system": req.system,
            "messages": req.messages,
        }
        if req.tools:
            kwargs["tools"] = req.tools

        response = await client.messages.create(**kwargs)

        replayed_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                replayed_text += block.text

        return {
            "original": {"text": req.original_response_text},
            "replayed": {
                "text": replayed_text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
            },
        }
    except Exception as e:
        logger.error("Replay failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
