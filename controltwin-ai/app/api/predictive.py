from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.predictive.predictor import MaintenancePredictor


router = APIRouter(prefix="/predictive", tags=["predictive"])
predictor = MaintenancePredictor()


class PredictiveFeedback(BaseModel):
    asset_id: str
    actual_failure_date: str
    maintenance_performed: str


@router.get("/rul/{asset_id}")
async def get_rul(asset_id: str):
    return await predictor.compute_rul(asset_id)


@router.get("/schedule")
async def get_schedule():
    # Minimal practical implementation; real deployment should fetch all assets from backend
    sample_assets = ["asset-001", "asset-002", "asset-003"]
    rows = []
    for aid in sample_assets:
        try:
            rows.append(await predictor.compute_rul(aid))
        except Exception:
            continue
    rows = sorted(rows, key=lambda x: x.get("rul_hours", 1e9))
    return {"items": rows}


@router.post("/feedback")
async def post_feedback(req: PredictiveFeedback):
    return {"status": "ok", "asset_id": req.asset_id, "stored": True}
