import logging
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agent.config import CONFIGS_DIR, load_business_config
from agent.loop import run_agent_loop
from agent.session import get_or_create_session

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

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


class BusinessInfo(BaseModel):
    business_id: str
    name: str


class CustomerInfo(BaseModel):
    customer_id: str
    name: str


@app.get("/businesses", response_model=list[BusinessInfo])
def list_businesses():
    results = []
    for path in sorted(CONFIGS_DIR.glob("*.yaml")):
        config = load_business_config(path.stem)
        results.append(BusinessInfo(business_id=config.business_id, name=config.name))
    return results


@app.get("/businesses/{business_id}/customers", response_model=list[CustomerInfo])
def list_customers(business_id: str):
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
