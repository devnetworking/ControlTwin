from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from influxdb_client import InfluxDBClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text

from app.core.config import get_settings


@dataclass
class AssetFeatures:
    operating_hours_total: float
    alerts_last_7d: int
    alerts_last_30d: int
    mean_temp_7d: float
    max_temp_7d: float
    temp_trend_slope: float
    mean_vibration_7d: float
    anomaly_score_mean_7d: float
    days_since_last_maintenance: float
    asset_age_days: float


class FeatureExtractor:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.influx = InfluxDBClient(
            url=self.settings.influx_url,
            token=self.settings.influx_token,
            org=self.settings.influx_org,
        )
        self.query_api = self.influx.query_api()
        self.engine = create_async_engine(self.settings.postgres_dsn, future=True, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def build_features(self, asset_id: str) -> AssetFeatures:
        async with self.session_factory() as session:
            alerts_7 = await session.execute(
                text("SELECT COUNT(*) FROM alerts WHERE asset_id=:a AND triggered_at >= now() - interval '7 days'"),
                {"a": asset_id},
            )
            alerts_30 = await session.execute(
                text("SELECT COUNT(*) FROM alerts WHERE asset_id=:a AND triggered_at >= now() - interval '30 days'"),
                {"a": asset_id},
            )
            asset_meta = await session.execute(
                text("SELECT commissioned_at, last_maintenance_at, operating_hours_total FROM assets WHERE id=:a"),
                {"a": asset_id},
            )
            row = asset_meta.first()
            commissioned_at = row[0] if row else None
            last_maint = row[1] if row else None
            operating_hours = float(row[2]) if row and row[2] is not None else 0.0

        temp_series = self._query_series(asset_id, "temperature", days=7)
        vib_series = self._query_series(asset_id, "vibration", days=7)
        anom_series = self._query_anomaly(asset_id, days=7)

        mean_temp = sum(temp_series) / len(temp_series) if temp_series else 0.0
        max_temp = max(temp_series) if temp_series else 0.0
        mean_vib = sum(vib_series) / len(vib_series) if vib_series else 0.0
        mean_anom = sum(anom_series) / len(anom_series) if anom_series else 0.0

        slope = 0.0
        if len(temp_series) > 1:
            slope = (temp_series[-1] - temp_series[0]) / max(1, len(temp_series) - 1)

        now = datetime.now(timezone.utc)
        days_since_maint = (now - last_maint).days if last_maint else 365.0
        age_days = (now - commissioned_at).days if commissioned_at else 365.0

        return AssetFeatures(
            operating_hours_total=operating_hours,
            alerts_last_7d=int(alerts_7.scalar() or 0),
            alerts_last_30d=int(alerts_30.scalar() or 0),
            mean_temp_7d=float(mean_temp),
            max_temp_7d=float(max_temp),
            temp_trend_slope=float(slope),
            mean_vibration_7d=float(mean_vib),
            anomaly_score_mean_7d=float(mean_anom),
            days_since_last_maintenance=float(days_since_maint),
            asset_age_days=float(age_days),
        )

    def _query_series(self, asset_id: str, metric: str, days: int) -> list[float]:
        flux = f'''
from(bucket: "{self.settings.influx_bucket}")
  |> range(start: -{days}d)
  |> filter(fn: (r) => r["asset_id"] == "{asset_id}" and r["metric"] == "{metric}")
  |> keep(columns: ["_value"])
'''
        tables = self.query_api.query(flux)
        values = []
        for t in tables:
            for r in t.records:
                try:
                    values.append(float(r.get_value()))
                except Exception:
                    continue
        return values

    def _query_anomaly(self, asset_id: str, days: int) -> list[float]:
        flux = f'''
from(bucket: "{self.settings.influx_anomaly_bucket}")
  |> range(start: -{days}d)
  |> filter(fn: (r) => r["asset_id"] == "{asset_id}" and r["_field"] == "final_score")
  |> keep(columns: ["_value"])
'''
        tables = self.query_api.query(flux)
        values = []
        for t in tables:
            for r in t.records:
                try:
                    values.append(float(r.get_value()))
                except Exception:
                    continue
        return values
