import logging

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent.config import load_business_config
from agent.loop import run_agent_loop
from agent.session import get_or_create_session

logger = logging.getLogger(__name__)

app = FastAPI(title="Customer Service Agent")


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


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    logger.info("[%s] customer=%s message: %s", req.business_id, req.customer_id, req.message)

    try:
        config = load_business_config(req.business_id)
    except FileNotFoundError:
        logger.warning("Business not found: %s", req.business_id)
        raise HTTPException(status_code=404, detail=f"Business '{req.business_id}' not found")

    history = get_or_create_session(req.business_id, req.customer_id)
    logger.info(
        "[%s] customer=%s history=%d messages",
        req.business_id,
        req.customer_id,
        len(history),
    )

    try:
        result = run_agent_loop(config, history, req.message, req.customer_id)
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
