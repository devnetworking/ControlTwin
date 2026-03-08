from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.simulation.simulator import TwinSimulator, SimulationConfig


router = APIRouter(prefix="/simulation", tags=["simulation"])
simulator = TwinSimulator()


class SimulationRequest(BaseModel):
    asset_id: str
    scenario_description: str = ""
    parameters: dict = {}
    n_iterations: int = 1000
    duration_hours: int = 24


@router.post("/run")
async def run_sim(req: SimulationRequest):
    cfg = SimulationConfig(
        asset_id=req.asset_id,
        scenario_description=req.scenario_description,
        parameters=req.parameters or {},
        n_iterations=req.n_iterations,
        duration_hours=req.duration_hours,
    )
    return await simulator.run_simulation(cfg)


@router.get("/{sim_id}/status")
async def sim_status(sim_id: str):
    return simulator.get_status(sim_id)


@router.get("/{sim_id}/results")
async def sim_results(sim_id: str):
    return simulator.get_results(sim_id)
