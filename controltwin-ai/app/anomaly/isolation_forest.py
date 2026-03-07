from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import joblib
import mlflow
import numpy as np
from influxdb_client import InfluxDBClient
from sklearn.ensemble import IsolationForest

from app.core.config import get_settings


class IsolationForestModel:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.model: IsolationForest | None = None
        self.model_version: str = "untrained"
        mlflow.set_tracking_uri(self.settings.mlflow_tracking_uri)
        os.makedirs(self.settings.model_dir, exist_ok=True)
        self.influx = InfluxDBClient(
            url=self.settings.influx_url,
            token=self.settings.influx_token,
            org=self.settings.influx_org,
        )
        self.query_api = self.influx.query_api()

    async def train(self, asset_id: str, data_point_ids: list[str], days: int = 30) -> dict[str, Any]:
        X = await self._build_matrix(asset_id=asset_id, data_point_ids=data_point_ids, days=days)
        if len(X) < 20:
            raise ValueError("Not enough samples for training IsolationForest")

        self.model = IsolationForest(contamination=self.settings.anomaly_iso_contamination, random_state=42)
        self.model.fit(X)

        model_path = os.path.join(self.settings.model_dir, f"{asset_id}_isolation_forest.pkl")
        joblib.dump(self.model, model_path)

        with mlflow.start_run(run_name=f"isolation_forest_{asset_id}"):
            mlflow.log_params({
                "asset_id": asset_id,
                "days": days,
                "contamination": self.settings.anomaly_iso_contamination,
                "n_samples": int(X.shape[0]),
                "n_features": int(X.shape[1]),
            })
            scores = self.model.decision_function(X)
            mlflow.log_metric("mean_decision_score", float(np.mean(scores)))
            mlflow.log_metric("std_decision_score", float(np.std(scores)))
            mlflow.log_artifact(model_path)

        self.model_version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return {"asset_id": asset_id, "model_path": model_path, "model_version": self.model_version}

    def predict(self, feature_vector: list[float]) -> float:
        if self.model is None:
            return 0.0
        x = np.array(feature_vector, dtype=float).reshape(1, -1)
        raw = float(self.model.decision_function(x)[0])  # usually around [-0.5, 0.5]
        score = max(0.0, min(1.0, (0.5 - raw)))
        return score

    def load_model(self, asset_id: str) -> bool:
        model_path = os.path.join(self.settings.model_dir, f"{asset_id}_isolation_forest.pkl")
        if not os.path.exists(model_path):
            return False
        self.model = joblib.load(model_path)
        self.model_version = os.path.basename(model_path)
        return True

    async def _build_matrix(self, asset_id: str, data_point_ids: list[str], days: int) -> np.ndarray:
        rows: list[list[float]] = []
        for dpid in data_point_ids:
            flux = f'''
from(bucket: "{self.settings.influx_bucket}")
  |> range(start: -{days}d)
  |> filter(fn: (r) => r["asset_id"] == "{asset_id}" and r["data_point_id"] == "{dpid}")
  |> keep(columns: ["_time","_value"])
'''
            tables = self.query_api.query(flux)
            values = []
            times = []
            for table in tables:
                for rec in table.records:
                    try:
                        values.append(float(rec.get_value()))
                        times.append(rec.get_time())
                    except Exception:
                        continue

            rolling_window = 12
            for i, v in enumerate(values):
                ts = times[i]
                hour = float(ts.hour)
                dow = float(ts.weekday())
                low = max(0, i - rolling_window + 1)
                rm = float(np.mean(values[low:i + 1]))
                rows.append([v, hour, dow, rm])

        return np.array(rows, dtype=float) if rows else np.empty((0, 4), dtype=float)
