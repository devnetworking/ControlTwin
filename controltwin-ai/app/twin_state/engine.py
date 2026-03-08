"""Digital Twin state engine backed by Redis."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Protocol

import redis.asyncio as aioredis

from app.core.config import get_settings


class PhysicalModelProtocol(Protocol):
    """Protocol for physical model implementations used in deviation computation."""

    async def expected_values(self, datapoints: list[dict[str, Any]]) -> dict[str, float]:
        """Return expected values for datapoint tags."""


class DigitalTwinEngine:
    """Engine handling synchronization and deviation analysis for asset twin states."""

    def __init__(self) -> None:
        """Initialize the engine and Redis client."""
        self.settings = get_settings()
        self.redis: aioredis.Redis = aioredis.from_url(self.settings.REDIS_URL, decode_responses=True)

    async def sync_asset(self, asset_id: str, datapoints: list[dict[str, Any]]) -> dict[str, Any]:
        """Sync incoming datapoints into Redis hash for a given asset."""
        try:
            key = f"twin:asset:{asset_id}"
            state_payload: dict[str, str] = {}
            for point in datapoints:
                tag = str(point.get("tag", "unknown"))
                state_payload[tag] = json.dumps(
                    {
                        "value": point.get("value"),
                        "timestamp": point.get("timestamp", datetime.now(timezone.utc).isoformat()),
                        "quality": point.get("quality", "good"),
                    }
                )
            if state_payload:
                await self.redis.hset(key, mapping=state_payload)
                await self.redis.expire(key, 3600)
            return {"asset_id": asset_id, "synced_points": len(state_payload)}
        except Exception as exc:
            return {"asset_id": asset_id, "synced_points": 0, "error": str(exc)}

    async def get_twin_state(self, asset_id: str) -> dict[str, Any]:
        """Read current twin state for an asset from Redis hash."""
        try:
            key = f"twin:asset:{asset_id}"
            raw_state = await self.redis.hgetall(key)
            parsed: dict[str, Any] = {}
            for tag, payload in raw_state.items():
                try:
                    parsed[tag] = json.loads(payload)
                except Exception:
                    parsed[tag] = {"raw": payload}
            return {"asset_id": asset_id, "state": parsed}
        except Exception as exc:
            return {"asset_id": asset_id, "state": {}, "error": str(exc)}

    async def compute_deviation(self, asset_id: str, physical_model: PhysicalModelProtocol) -> dict[str, Any]:
        """Compare real twin values against expected physical model values."""
        try:
            twin_state = await self.get_twin_state(asset_id)
            state = twin_state.get("state", {})
            datapoints = [{"tag": tag, **payload} for tag, payload in state.items() if isinstance(payload, dict)]
            expected = await physical_model.expected_values(datapoints)

            deviations: list[dict[str, Any]] = []
            for tag, payload in state.items():
                if tag not in expected:
                    continue
                try:
                    real = float(payload.get("value", 0.0))
                    exp = float(expected[tag])
                    delta = real - exp
                    deviations.append(
                        {
                            "tag": tag,
                            "real": real,
                            "expected": exp,
                            "deviation": delta,
                            "abs_deviation": abs(delta),
                        }
                    )
                except Exception:
                    continue

            return {"asset_id": asset_id, "deviations": deviations}
        except Exception as exc:
            return {"asset_id": asset_id, "deviations": [], "error": str(exc)}
