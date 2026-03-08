from __future__ import annotations

import asyncio
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket
from pydantic import BaseModel

from app.twin_state.engine import TwinStateEngine


router = APIRouter(prefix="/twin-state", tags=["twin-state"])
engine = TwinStateEngine()


class DesiredStateRequest(BaseModel):
    state: dict[str, float]
    set_by_user_id: str


@router.get("/{asset_id}")
async def get_twin_state(asset_id: str):
    await engine.init_db()
    state = await engine.get_state(asset_id)
    if not state:
        raise HTTPException(status_code=404, detail="asset_not_found")
    overall_status = "unknown"
    if state.get("reported_state") and state.get("desired_state"):
        overall_status = "diverged" if state.get("divergences") else "synced"
    return {**state, "overall_status": overall_status}


@router.post("/desired-state/{asset_id}")
async def set_desired_state(asset_id: str, req: DesiredStateRequest):
    await engine.init_db()
    divs = await engine.set_desired(asset_id=asset_id, desired_state=req.state, user_id=req.set_by_user_id)
    state = await engine.get_state(asset_id)
    return {"asset_id": asset_id, "divergences": divs, "state": state}


@router.get("/{asset_id}/divergences")
async def get_divergences(asset_id: str):
    await engine.init_db()
    state = await engine.get_state(asset_id)
    if not state:
        raise HTTPException(status_code=404, detail="asset_not_found")
    return {"asset_id": asset_id, "divergences": state.get("divergences", [])}


@router.websocket("/ws/{asset_id}")
async def twin_state_ws(websocket: WebSocket, asset_id: str):
    await websocket.accept()
    await engine.init_db()
    try:
        while True:
            state = await engine.get_state(asset_id)
            await websocket.send_json(state or {"asset_id": asset_id, "reported_state": {}, "desired_state": {}, "divergences": []})
            await asyncio.sleep(2)
    except Exception:
        await websocket.close()
