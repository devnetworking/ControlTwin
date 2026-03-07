from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter
from pydantic import BaseModel

from app.anomaly.detector import AnomalyDetector


router = APIRouter(prefix="/anomaly", tags=["anomaly"])
detector = AnomalyDetector()


class FeedbackRequest(BaseModel):
    alert_id: str
    is_false_positive: bool
    comment: str


@router.get("/score/{data_point_id}")
async def get_score(data_point_id: str):
    cached = await detector.get_latest_score(data_point_id)
    if cached:
        return cached
    return {
        "data_point_id": data_point_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level1_breach": False,
        "level2_zscore": 0.0,
        "level3_isolation_score": 0.0,
        "level4_lstm_error": 0.0,
        "final_score": 0.0,
        "is_anomaly": False,
        "confidence": 0.5,
        "model_version": "unknown",
    }


@router.get("/history/{asset_id}")
async def get_history(asset_id: str, hours: int = 24):
    rows = await detector.get_history(asset_id=asset_id, hours=hours)
    return {"asset_id": asset_id, "hours": hours, "series": rows}


@router.get("/alerts")
async def get_recent_alerts():
    return {"items": await detector.get_recent_alerts()}


@router.post("/feedback")
async def post_feedback(req: FeedbackRequest):
    return await detector.record_feedback(req.alert_id, req.is_false_positive, req.comment)
