from __future__ import annotations

import json
from statistics import mean, pstdev
from typing import Any

from influxdb_client import InfluxDBClient
from redis.asyncio import from_url as redis_from_url

from app.core.config import get_settings


class BaselineCalculator:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.redis = redis_from_url(self.settings.redis_url, decode_responses=True)
        self.influx = InfluxDBClient(
            url=self.settings.influx_url,
            token=self.settings.influx_token,
            org=self.settings.influx_org,
        )
        self.query_api = self.influx.query_api()

    async def get_baseline(self, data_point_id: str) -> dict[str, Any]:
        cache_key = f"baseline:{data_point_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)

        flux = f'''
from(bucket: "{self.settings.influx_bucket}")
  |> range(start: -30d)
  |> filter(fn: (r) => r["data_point_id"] == "{data_point_id}")
  |> keep(columns: ["_value"])
'''
        records = self.query_api.query(flux)
        values: list[float] = []
        for table in records:
            for rec in table.records:
                try:
                    values.append(float(rec.get_value()))
                except Exception:
                    continue

        if not values:
            baseline = {"mean": 0.0, "std": 1.0, "p5": 0.0, "p95": 0.0, "count": 0}
        else:
            sorted_vals = sorted(values)
            p5_idx = max(0, int(0.05 * (len(sorted_vals) - 1)))
            p95_idx = max(0, int(0.95 * (len(sorted_vals) - 1)))
            baseline = {
                "mean": float(mean(values)),
                "std": float(pstdev(values) or 1.0),
                "p5": float(sorted_vals[p5_idx]),
                "p95": float(sorted_vals[p95_idx]),
                "count": len(values),
            }

        await self.redis.set(cache_key, json.dumps(baseline), ex=6 * 3600)
        return baseline

    async def update_rolling_features(self, data_point_id: str, new_value: float) -> None:
        key = f"features:{data_point_id}"
        await self.redis.rpush(key, float(new_value))
        await self.redis.ltrim(key, -60, -1)

        values = await self.redis.lrange(key, 0, -1)
        vals = [float(v) for v in values] if values else [float(new_value)]
        m = float(mean(vals))
        s = float(pstdev(vals) or 0.0)

        await self.redis.hset(
            f"features_stats:{data_point_id}",
            mapping={"rolling_mean_1h": m, "rolling_std_1h": s, "count": len(vals)},
        )
