from __future__ import annotations

import math
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import get_settings
from app.simulation.physical_models import PhysicalModels
from app.simulation.scenario_generator import ScenarioGenerator


@dataclass
class SimulationConfig:
    asset_id: str
    scenario_description: str
    parameters: dict[str, Any]
    n_iterations: int = 1000
    duration_hours: int = 24


class TwinSimulator:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.generator = ScenarioGenerator()
        self.results: dict[str, dict[str, Any]] = {}
        self.status: dict[str, dict[str, Any]] = {}

    async def run_simulation(self, config: SimulationConfig) -> dict[str, Any]:
        sim_id = str(uuid.uuid4())
        self.status[sim_id] = {"status": "running", "progress_pct": 0}

        asset = await self._fetch_backend(f"/assets/{config.asset_id}")
        twin_state = await self._fetch_ai_twin_state(config.asset_id)

        params = config.parameters or {}
        if config.scenario_description and not params:
            generated = await self.generator.generate(config.scenario_description, asset, twin_state)
            params = generated.get("parameter_overrides", {})
            config.n_iterations = int(generated.get("n_iterations", config.n_iterations))
            config.duration_hours = int(generated.get("duration_hours", config.duration_hours))

        breaches = 0
        times_to_breach = []
        affected_assets = {}
        dist = {}
        trajectories = []

        for i in range(max(1, config.n_iterations)):
            nominal_temp = float(params.get("temp", 65.0))
            nominal_pressure = float(params.get("pressure_inlet", 40.0))
            temp = nominal_temp + random.gauss(0, 2)
            pressure_out = PhysicalModels.pipeline_pressure(
                inlet_pressure_bar=nominal_pressure,
                flow_rate_m3h=float(params.get("flow_rate_m3h", 120)),
                pipe_length_km=float(params.get("pipe_length_km", 15)),
                pipe_diameter_mm=float(params.get("pipe_diameter_mm", 300)),
            )
            thermal = PhysicalModels.thermal_model(
                initial_temp_c=temp,
                ambient_temp_c=float(params.get("ambient_temp_c", 28)),
                heat_generation_kw=float(params.get("heat_generation_kw", 10)),
                thermal_resistance=float(params.get("thermal_resistance", 0.3)),
                thermal_capacity=float(params.get("thermal_capacity", 15000)),
                time_steps_minutes=config.duration_hours * 60,
            )

            breach_time = None
            for minute, t in enumerate(thermal):
                if t > float(params.get("temp_threshold", 95.0)) or pressure_out < float(params.get("pressure_min", 8.0)):
                    breach_time = minute / 60.0
                    break

            if breach_time is not None:
                breaches += 1
                times_to_breach.append(breach_time)
                affected_assets[config.asset_id] = affected_assets.get(config.asset_id, 0) + 1
                bucket = f"{int(math.floor(breach_time))}h"
                dist[bucket] = dist.get(bucket, 0) + 1

            trajectories.append({"time": i, "values": {"max_temp": max(thermal), "pressure_out": pressure_out}})

            if i % 20 == 0:
                self.status[sim_id] = {"status": "running", "progress_pct": int((i / config.n_iterations) * 100)}

        prob = breaches / max(1, config.n_iterations)
        mean_ttb = sum(times_to_breach) / len(times_to_breach) if times_to_breach else float(config.duration_hours)
        ci_low = max(0.0, prob - 1.96 * math.sqrt(prob * (1 - prob) / max(1, config.n_iterations)))
        ci_high = min(1.0, prob + 1.96 * math.sqrt(prob * (1 - prob) / max(1, config.n_iterations)))
        worst_case = min(times_to_breach) if times_to_breach else float(config.duration_hours)

        out = {
            "simulation_id": sim_id,
            "asset_id": config.asset_id,
            "scenario_description": config.scenario_description,
            "probability_of_failure": prob,
            "mean_time_to_breach_hours": mean_ttb,
            "confidence_interval_95": [ci_low, ci_high],
            "affected_assets": [{"asset_id": k, "probability": v / max(1, config.n_iterations)} for k, v in affected_assets.items()],
            "worst_case": {"description": "Earliest threshold breach", "time_to_breach_hours": worst_case},
            "monte_carlo_distribution": [{"bucket": k, "count": v} for k, v in sorted(dist.items())],
            "physical_model_trajectory": trajectories[:200],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "safety_notice": "suggestions_only_no_auto_execution",
        }
        self.results[sim_id] = out
        self.status[sim_id] = {"status": "completed", "progress_pct": 100}
        return {"simulation_id": sim_id}

    def get_status(self, sim_id: str) -> dict[str, Any]:
        return self.status.get(sim_id, {"status": "pending", "progress_pct": 0})

    def get_results(self, sim_id: str) -> dict[str, Any]:
        return self.results.get(sim_id, {"error": "simulation_not_found"})

    async def _fetch_backend(self, suffix: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self.settings.backend_base_url}{suffix}")
                if r.status_code == 200:
                    return r.json()
        except Exception:
            pass
        return {}

    async def _fetch_ai_twin_state(self, asset_id: str) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"http://localhost:8001/api/v1/ai/twin-state/{asset_id}")
                if r.status_code == 200:
                    return r.json()
        except Exception:
            pass
        return {"reported_state": {}}
