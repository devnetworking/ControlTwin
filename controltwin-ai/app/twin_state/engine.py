from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import get_settings
from app.core.logging import get_logger
from app.twin_state.models import Base, TwinState, StateHistory
from app.twin_state.reconciler import LLMReconciler


class TwinStateEngine:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger("controltwin-ai.twin-state")
        self.engine = create_async_engine(self.settings.postgres_dsn, future=True, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)
        self.reconciler = LLMReconciler()

    async def init_db(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def update_reported(self, asset_id: str, data_point_tag: str, value: float, timestamp: datetime, quality: str = "good", source: str | None = None) -> dict:
        async with self.session_factory() as session:
            state = await session.get(TwinState, asset_id)
            if state is None:
                state = TwinState(asset_id=asset_id, reported_state={}, desired_state={}, divergences=[])
                session.add(state)

            reported = dict(state.reported_state or {})
            reported[data_point_tag] = {
                "value": value,
                "timestamp": timestamp.isoformat(),
                "quality": quality,
            }
            state.reported_state = reported
            state.last_reported_at = timestamp
            state.updated_at = datetime.now(timezone.utc)

            session.add(StateHistory(
                asset_id=asset_id,
                state_type="reported",
                state={data_point_tag: reported[data_point_tag]},
                source=source,
            ))

            await session.commit()

        divergences = await self.check_divergence(asset_id)
        return {"asset_id": asset_id, "divergences": divergences}

    async def set_desired(self, asset_id: str, desired_state: dict[str, Any], user_id: str) -> dict:
        now = datetime.now(timezone.utc)
        async with self.session_factory() as session:
            state = await session.get(TwinState, asset_id)
            if state is None:
                state = TwinState(asset_id=asset_id, reported_state={}, desired_state={}, divergences=[])
                session.add(state)

            existing = dict(state.desired_state or {})
            for k, v in desired_state.items():
                existing[k] = {"value": v, "set_by": user_id, "set_at": now.isoformat()}
            state.desired_state = existing
            state.last_desired_at = now
            state.updated_at = now

            session.add(StateHistory(
                asset_id=asset_id,
                state_type="desired",
                state=desired_state,
                source=user_id,
            ))

            await session.commit()

        divergences = await self.check_divergence(asset_id)
        return {"asset_id": asset_id, "divergences": divergences}

    async def check_divergence(self, asset_id: str) -> list[dict[str, Any]]:
        threshold = self.settings.divergence_threshold_pct / 100.0
        now = datetime.now(timezone.utc)

        async with self.session_factory() as session:
            state = await session.get(TwinState, asset_id)
            if state is None:
                return []

            reported = state.reported_state or {}
            desired = state.desired_state or {}

            divergences: list[dict[str, Any]] = []
            for tag, desired_payload in desired.items():
                if tag not in reported:
                    continue
                try:
                    desired_value = float(desired_payload["value"] if isinstance(desired_payload, dict) else desired_payload)
                    reported_value = float(reported[tag]["value"] if isinstance(reported[tag], dict) else reported[tag])
                except Exception:
                    continue
                if desired_value == 0:
                    continue

                delta = abs(reported_value - desired_value) / abs(desired_value)
                if delta > threshold:
                    set_at = desired_payload.get("set_at") if isinstance(desired_payload, dict) else None
                    duration_minutes = 0.0
                    if set_at:
                        try:
                            dt = datetime.fromisoformat(set_at)
                            duration_minutes = (now - dt).total_seconds() / 60
                        except Exception:
                            duration_minutes = 0.0
                    divergences.append({
                        "tag": tag,
                        "reported": reported_value,
                        "desired": desired_value,
                        "delta_pct": round(delta * 100, 4),
                        "duration_minutes": round(duration_minutes, 2),
                    })

            state.divergences = divergences
            state.updated_at = now

            critical = any(d["duration_minutes"] >= self.settings.divergence_critical_minutes for d in divergences)
            if critical and divergences:
                explanation = await self.reconciler.explain_divergence(
                    asset={"name": asset_id, "asset_type": "unknown", "site_name": "unknown", "protocol": "unknown", "ip_address": "unknown", "purdue_level": "unknown"},
                    divergences=divergences,
                    context=[],
                )
                state.llm_explanation = explanation

            await session.commit()

            if critical and divergences:
                await self._create_backend_alert(asset_id, divergences)

            return divergences

    async def get_state(self, asset_id: str) -> dict[str, Any]:
        async with self.session_factory() as session:
            state = await session.get(TwinState, asset_id)
            if state is None:
                return {
                    "asset_id": asset_id,
                    "reported_state": {},
                    "desired_state": {},
                    "divergences": [],
                    "last_updated": None,
                    "overall_status": "unknown",
                }

            overall = "synced" if not state.divergences else "diverged"
            return {
                "asset_id": state.asset_id,
                "reported_state": state.reported_state or {},
                "desired_state": state.desired_state or {},
                "divergences": state.divergences or [],
                "last_updated": state.updated_at.isoformat() if state.updated_at else None,
                "overall_status": overall,
                "llm_explanation": state.llm_explanation,
            }

    async def get_divergences(self, asset_id: str) -> dict[str, Any]:
        data = await self.get_state(asset_id)
        return {
            "asset_id": asset_id,
            "divergences": data.get("divergences", []),
            "llm_explanation": data.get("llm_explanation"),
        }

    async def _create_backend_alert(self, asset_id: str, divergences: list[dict[str, Any]]) -> None:
        url = f"{self.settings.backend_base_url}/alerts"
        payload = {
            "asset_id": asset_id,
            "title": "Digital Twin divergence detected",
            "category": "process_integrity",
            "severity": "high",
            "description": f"Detected {len(divergences)} persistent divergence(s)",
            "raw_data": {"divergences": divergences},
            "source": "controltwin-ai",
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(url, json=payload)
        except Exception:
            self.logger.exception("failed creating backend alert", extra={"event": "backend_alert_failed", "asset_id": asset_id})
