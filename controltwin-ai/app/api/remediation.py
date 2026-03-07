from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.remediation.engine import RemediationEngine


router = APIRouter(prefix="/remediation", tags=["remediation"])
engine = RemediationEngine()


class SuggestRequest(BaseModel):
    alert_id: str
    asset_id: str


class FeedbackRequest(BaseModel):
    suggestion_id: str
    was_helpful: bool
    applied_action: str
    outcome: str


@router.post("/suggest")
async def suggest(req: SuggestRequest):
    await engine.init_db()
    return await engine.suggest(alert_id=req.alert_id, asset_id=req.asset_id, context={})


@router.post("/feedback")
async def feedback(req: FeedbackRequest):
    await engine.init_db()
    return await engine.add_feedback(
        suggestion_id=req.suggestion_id,
        was_helpful=req.was_helpful,
        applied_action=req.applied_action,
        outcome=req.outcome,
    )


@router.get("/history/{alert_id}")
async def history(alert_id: str):
    await engine.init_db()
    return {"items": await engine.history(alert_id)}
