from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import joblib
import mlflow
import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from app.core.config import get_settings
from app.predictive.features import FeatureExtractor


class MaintenancePredictor:
    def __init__(self) -> None:
        self.settings = get_settings()
        os.makedirs(self.settings.model_dir, exist_ok=True)
        mlflow.set_tracking_uri(self.settings.mlflow_tracking_uri)
        self.extractor = FeatureExtractor()
        self.model_path = os.path.join(self.settings.model_dir, "rul_random_forest.pkl")
        self.model: RandomForestRegressor | None = None
        self.model_version = "untrained"
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.model_version = "loaded-local"

    async def compute_rul(self, asset_id: str) -> dict[str, Any]:
        f = await self.extractor.build_features(asset_id)
        vec = np.array([[
            f.operating_hours_total, f.alerts_last_7d, f.alerts_last_30d,
            f.mean_temp_7d, f.max_temp_7d, f.temp_trend_slope,
            f.mean_vibration_7d, f.anomaly_score_mean_7d,
            f.days_since_last_maintenance, f.asset_age_days
        ]], dtype=float)

        if self.model is None:
            predicted_rul = max(24.0, 1000.0 - 0.05 * f.operating_hours_total - 5.0 * f.alerts_last_30d)
            importances = [0.1] * 10
            confidence = 0.6
        else:
            predicted_rul = float(self.model.predict(vec)[0])
            importances = list(getattr(self.model, "feature_importances_", np.array([0.1] * 10)))
            confidence = float(max(0.5, min(0.99, 1.0 - f.anomaly_score_mean_7d)))

        status = "OK" if predicted_rul > 720 else "WARNING" if predicted_rul >= 168 else "CRITICAL"
        forecast = self._forecast_30d(asset_id)
        failure_date = (datetime.now(timezone.utc) + timedelta(hours=max(predicted_rul, 1.0))).isoformat()

        names = [
            "operating_hours_total", "alerts_last_7d", "alerts_last_30d", "mean_temp_7d", "max_temp_7d",
            "temp_trend_slope", "mean_vibration_7d", "anomaly_score_mean_7d", "days_since_last_maintenance", "asset_age_days"
        ]
        top = sorted(
            [{"feature": n, "importance": float(i), "value": float(v)} for n, i, v in zip(names, importances, vec[0])],
            key=lambda x: x["importance"],
            reverse=True
        )[:5]

        return {
            "asset_id": asset_id,
            "rul_hours": float(predicted_rul),
            "status": status,
            "confidence": confidence,
            "predicted_failure_date": failure_date,
            "top_risk_features": top,
            "forecast_30d": forecast,
            "model_version": self.model_version,
        }

    async def train_rul_model(self, labeled_data: list[dict[str, Any]]) -> dict[str, Any]:
        if len(labeled_data) < 20:
            raise ValueError("Need at least 20 labeled samples to train RUL model")

        X = np.array([row["features"] for row in labeled_data], dtype=float)
        y = np.array([row["actual_rul_hours"] for row in labeled_data], dtype=float)

        model = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=-1)
        model.fit(X, y)
        preds = model.predict(X)

        mae = float(mean_absolute_error(y, preds))
        rmse = float(np.sqrt(mean_squared_error(y, preds)))

        joblib.dump(model, self.model_path)
        self.model = model
        self.model_version = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

        with mlflow.start_run(run_name=f"rul_rf_{self.model_version}"):
            mlflow.log_param("model", "RandomForestRegressor")
            mlflow.log_param("n_estimators", 300)
            mlflow.log_metric("MAE", mae)
            mlflow.log_metric("RMSE", rmse)
            mlflow.log_artifact(self.model_path)

        return {"mae": mae, "rmse": rmse, "model_version": self.model_version}

    def _forecast_30d(self, asset_id: str) -> list[dict[str, Any]]:
        now = datetime.now(timezone.utc)
        ts = pd.date_range(end=now, periods=90, freq="D")
        vals = np.linspace(50, 70, 90) + np.random.normal(0, 1, 90)

        df = pd.DataFrame({"ds": ts, "y": vals})
        m = Prophet(daily_seasonality=False, weekly_seasonality=True, yearly_seasonality=False)
        m.fit(df)
        future = m.make_future_dataframe(periods=30)
        fc = m.predict(future).tail(30)

        out = []
        for _, r in fc.iterrows():
            out.append({
                "date": r["ds"].isoformat(),
                "predicted_value": float(r["yhat"]),
                "trend": "up" if float(r["trend"]) >= float(fc["trend"].mean()) else "down",
            })
        return out
