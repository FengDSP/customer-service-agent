from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent.config import load_business_config
from agent.loop import run_agent_loop
from agent.session import get_or_create_session

app = FastAPI(title="Customer Service Agent")


class ChatRequest(BaseModel):
    session_id: str | None = None
    business_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        config = load_business_config(req.business_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Business '{req.business_id}' not found")

    session_id, history = get_or_create_session(req.session_id)

    try:
        reply = run_agent_loop(config, history, req.message, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(session_id=session_id, reply=reply)
