from __future__ import annotations

import asyncio
from typing import Any

import httpx
from celery import Celery
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.anomaly.isolation_forest import IsolationForestModel
from app.anomaly.baseline import BaselineCalculator
from app.core.config import get_settings
from app.remediation.knowledge_base.indexer import KBIndexer
from app.predictive.predictor import MaintenancePredictor


settings = get_settings()
celery_app = Celery("controltwin_ai", broker=settings.redis_url)


async def _list_assets() -> list[dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.get(f"{settings.backend_base_url}/assets")
            if r.status_code == 200:
                data = r.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict) and "items" in data:
                    return data["items"]
    except Exception:
        pass
    return []


@celery_app.task
def retrain_models():
    async def _run():
        assets = await _list_assets()
        model = IsolationForestModel()
        retrained = 0
        for a in assets:
            aid = str(a.get("id"))
            dps = [str(dp.get("id")) for dp in a.get("data_points", []) if dp.get("id")]
            if len(dps) >= 1:
                try:
                    await model.train(asset_id=aid, data_point_ids=dps, days=30)
                    retrained += 1
                except Exception:
                    continue
        return {"status": "ok", "retrained_assets": retrained}
    return asyncio.run(_run())


@celery_app.task
def compute_rul_all_assets():
    async def _run():
        assets = await _list_assets()
        predictor = MaintenancePredictor()

        engine = create_async_engine(settings.postgres_dsn, future=True, echo=False)
        sf = async_sessionmaker(engine, expire_on_commit=False)

        async with engine.begin() as conn:
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS ai_rul_predictions (
                    id SERIAL PRIMARY KEY,
                    asset_id VARCHAR(128) NOT NULL,
                    rul_hours DOUBLE PRECISION NOT NULL,
                    status VARCHAR(32) NOT NULL,
                    confidence DOUBLE PRECISION NOT NULL,
                    model_version VARCHAR(128),
                    payload JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                )
            """))

        count = 0
        async with sf() as session:
            for a in assets:
                aid = str(a.get("id"))
                try:
                    pred = await predictor.compute_rul(aid)
                except Exception:
                    continue
                await session.execute(
                    text("""
                        INSERT INTO ai_rul_predictions (asset_id, rul_hours, status, confidence, model_version, payload)
                        VALUES (:aid, :rul, :status, :conf, :mv, CAST(:payload AS JSONB))
                    """),
                    {
                        "aid": aid,
                        "rul": pred["rul_hours"],
                        "status": pred["status"],
                        "conf": pred["confidence"],
                        "mv": pred.get("model_version"),
                        "payload": __import__("json").dumps(pred),
                    },
                )
                count += 1
            await session.commit()

        await engine.dispose()
        return {"status": "ok", "computed_assets": count}
    return asyncio.run(_run())


@celery_app.task
def update_baselines():
    async def _run():
        calc = BaselineCalculator()
        assets = await _list_assets()
        refreshed = 0
        for a in assets:
            for dp in a.get("data_points", []):
                dpid = str(dp.get("id"))
                if not dpid:
                    continue
                try:
                    await calc.get_baseline(dpid)
                    refreshed += 1
                except Exception:
                    continue
        return {"status": "ok", "refreshed_datapoints": refreshed}
    return asyncio.run(_run())


@celery_app.task
def index_knowledge_base():
    async def _run():
        idx = KBIndexer()
        total = await idx.index_mitre_ics()
        return {"status": "ok", "indexed_chunks": total}
    return asyncio.run(_run())
