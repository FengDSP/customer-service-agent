from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent.config import load_business_config
from agent.loop import run_agent_loop
from agent.session import get_or_create_session

app = FastAPI(title="Customer Service Agent")


class ChatRequest(BaseModel):
    business_id: str
    customer_id: str
    message: str


class ChatResponse(BaseModel):
    customer_id: str
    reply: str


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        config = load_business_config(req.business_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Business '{req.business_id}' not found")

    history = get_or_create_session(req.customer_id)

    try:
        reply = run_agent_loop(config, history, req.message, req.customer_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(customer_id=req.customer_id, reply=reply)
