from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from influxdb_client import InfluxDBClient
from redis.asyncio import from_url as redis_from_url

from app.anomaly.baseline import BaselineCalculator
from app.anomaly.isolation_forest import IsolationForestModel
from app.anomaly.lstm_autoencoder import LSTMAnomalyModel
from app.anomaly.mitre_mapper import MitreMapper
from app.core.config import get_settings
from app.core.logging import get_logger


class AnomalyDetector:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger("controltwin-ai.anomaly")
        self.baseline = BaselineCalculator()
        self.iso = IsolationForestModel()
        self.lstm = LSTMAnomalyModel()
        self.mapper = MitreMapper()
        self.redis = redis_from_url(self.settings.redis_url, decode_responses=True)
        self.influx = InfluxDBClient(
            url=self.settings.influx_url,
            token=self.settings.influx_token,
            org=self.settings.influx_org,
        )
        self.write_api = self.influx.write_api()

    async def process_datapoint(self, datapoint: dict[str, Any]) -> dict[str, Any]:
        value = float(datapoint.get("value", 0))
        data_point_id = str(datapoint.get("data_point_id"))
        asset_id = str(datapoint.get("asset_id"))
        asset_type = str(datapoint.get("asset_type", "unknown"))
        timestamp = datapoint.get("timestamp") or datetime.now(timezone.utc).isoformat()

        level1_breach = self._level1_rules(datapoint, value)
        baseline = await self.baseline.get_baseline(data_point_id)
        level2_zscore = self._zscore(value, baseline.get("mean", 0), baseline.get("std", 1))
        level2_score = 0.0
        if abs(level2_zscore) > 4:
            level2_score = 0.95
        elif abs(level2_zscore) > 3:
            level2_score = 0.8

        feature_vec = await self._feature_vector(data_point_id, value)
        level3_iso_score = self.iso.predict(feature_vec) if self.iso.model else 0.0

        seq = await self._sequence(data_point_id, value)
        level4_lstm_error = 0.0
        level4_score = 0.0
        if self.lstm.model:
            is_anom, err = self.lstm.predict(seq)
            level4_lstm_error = err
            level4_score = min(1.0, err * 10) if is_anom else min(0.5, err * 5)

        level1_score = 1.0 if level1_breach else 0.0
        final_score = 0.35 * level1_score + 0.25 * level2_score + 0.2 * level3_iso_score + 0.2 * level4_score
        is_anomaly = final_score > self.settings.anomaly_final_threshold

        anomaly_type = "threshold_breach" if level1_breach else "baseline_deviation"
        technique = self.mapper.map(anomaly_type, asset_type, {"sudden": abs(level2_zscore) > 4})

        result = {
            "data_point_id": data_point_id,
            "asset_id": asset_id,
            "timestamp": timestamp,
            "level1_breach": level1_breach,
            "level2_zscore": float(level2_zscore),
            "level3_isolation_score": float(level3_iso_score),
            "level4_lstm_error": float(level4_lstm_error),
            "final_score": float(final_score),
            "is_anomaly": bool(is_anomaly),
            "mitre_technique": technique,
            "model_version": {
                "isolation_forest": self.iso.model_version,
                "lstm_autoencoder": self.lstm.model_version,
            },
            "confidence": min(0.99, max(0.5, final_score)),
        }

        await self.baseline.update_rolling_features(data_point_id, value)
        await self._store_score(result)

        if is_anomaly:
            await self._create_alert(result)

        return result

    def _level1_rules(self, datapoint: dict[str, Any], value: float) -> bool:
        quality = str(datapoint.get("quality", "good")).lower()
        if quality == "bad":
            return True

        ll = datapoint.get("alarm_low_low")
        lo = datapoint.get("alarm_low")
        hi = datapoint.get("alarm_high")
        hh = datapoint.get("alarm_high_high")
        checks = [
            ll is not None and value < float(ll),
            lo is not None and value < float(lo),
            hi is not None and value > float(hi),
            hh is not None and value > float(hh),
        ]
        return any(checks)

    def _zscore(self, value: float, m: float, s: float) -> float:
        if not s:
            return 0.0
        return (value - m) / s

    async def _feature_vector(self, data_point_id: str, new_value: float) -> list[float]:
        vals = await self.redis.lrange(f"features:{data_point_id}", -10, -1)
        vec = [float(v) for v in vals] if vals else []
        while len(vec) < 9:
            vec.append(float(new_value))
        vec.append(float(new_value))
        return vec[:10]

    async def _sequence(self, data_point_id: str, new_value: float):
        vals = await self.redis.lrange(f"features:{data_point_id}", -60, -1)
        arr = [float(v) for v in vals] if vals else []
        arr.append(float(new_value))
        arr = arr[-60:]
        while len(arr) < 60:
            arr.insert(0, arr[0] if arr else float(new_value))
        import numpy as np
        return np.array(arr, dtype=float).reshape(60, 1)

    async def _store_score(self, result: dict[str, Any]) -> None:
        from influxdb_client import Point
        p = (
            Point("anomaly_score")
            .tag("data_point_id", result["data_point_id"])
            .tag("asset_id", result["asset_id"])
            .field("final_score", float(result["final_score"]))
            .field("level2_zscore", float(result["level2_zscore"]))
            .field("level3_isolation_score", float(result["level3_isolation_score"]))
            .field("level4_lstm_error", float(result["level4_lstm_error"]))
            .field("is_anomaly", 1 if result["is_anomaly"] else 0)
        )
        self.write_api.write(bucket=self.settings.influx_anomaly_bucket, org=self.settings.influx_org, record=p)

    async def _create_alert(self, result: dict[str, Any]) -> None:
        payload = {
            "asset_id": result["asset_id"],
            "title": "ML anomaly detected",
            "category": "anomaly_detection",
            "severity": "high" if result["final_score"] > 0.9 else "medium",
            "description": f"Anomaly score {result['final_score']:.3f} on datapoint {result['data_point_id']}",
            "mitre_technique_id": result["mitre_technique"]["id"],
            "mitre_technique_name": result["mitre_technique"]["name"],
            "raw_data": result,
            "source": "controltwin-ai",
        }
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                await client.post(f"{self.settings.backend_base_url}/alerts", json=payload)
        except Exception:
            self.logger.exception("failed posting anomaly alert")
