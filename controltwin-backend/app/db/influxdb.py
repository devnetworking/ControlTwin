"""InfluxDB repository for time-series operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from app.core.config import settings


class InfluxRepository:
    """Repository for InfluxDB operations."""

    def __init__(self) -> None:
        self.client = InfluxDBClient(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG,
        )
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.realtime_bucket = settings.INFLUXDB_BUCKET_REALTIME
        self.history_bucket = settings.INFLUXDB_BUCKET_HISTORY

    def close(self) -> None:
        """Close InfluxDB client."""
        self.client.close()

    def write_measurement(
        self,
        bucket: str,
        measurement: str,
        site_id: str,
        asset_id: str,
        data_point_id: str,
        tag: str,
        quality: str,
        value: Any,
        timestamp_ms: int | None = None,
    ) -> None:
        """Write a single measurement point."""
        point = (
            Point(measurement)
            .tag("site_id", site_id)
            .tag("asset_id", asset_id)
            .tag("data_point_id", data_point_id)
            .tag("tag", tag)
            .tag("quality", quality)
        )

        if isinstance(value, bool):
            point = point.field("value_bool", value)
        elif isinstance(value, (int, float)):
            point = point.field("value", float(value))
        else:
            point = point.field("value_str", str(value))

        if timestamp_ms is not None:
            point = point.time(timestamp_ms, WritePrecision.MS)
        else:
            now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
            point = point.time(now_ms, WritePrecision.MS)

        self.write_api.write(bucket=bucket, org=settings.INFLUXDB_ORG, record=point)

    def write_batch(self, bucket: str, records: list[dict[str, Any]]) -> None:
        """Write a batch of records."""
        points: list[Point] = []
        for rec in records:
            point = (
                Point(rec.get("measurement", "ics_datapoint"))
                .tag("site_id", rec["site_id"])
                .tag("asset_id", rec["asset_id"])
                .tag("data_point_id", rec["data_point_id"])
                .tag("tag", rec["tag"])
                .tag("quality", rec.get("quality", "good"))
            )
            value = rec.get("value")
            if isinstance(value, bool):
                point = point.field("value_bool", value)
            elif isinstance(value, (int, float)):
                point = point.field("value", float(value))
            else:
                point = point.field("value_str", str(value))

            timestamp_ms = rec.get("timestamp_ms", int(datetime.now(timezone.utc).timestamp() * 1000))
            point = point.time(timestamp_ms, WritePrecision.MS)
            points.append(point)

        self.write_api.write(bucket=bucket, org=settings.INFLUXDB_ORG, record=points)

    def query_measurements(
        self,
        bucket: str,
        data_point_ids: list[str],
        start: datetime,
        stop: datetime,
        aggregate_window: str | None = None,
        aggregate_fn: str = "mean",
    ) -> list[dict[str, Any]]:
        """Query measurements via Flux with optional aggregateWindow."""
        ids_filter = " or ".join([f'r["data_point_id"] == "{dp_id}"' for dp_id in data_point_ids])
        flux = f'''
from(bucket: "{bucket}")
  |> range(start: {start.isoformat()}, stop: {stop.isoformat()})
  |> filter(fn: (r) => {ids_filter})
'''
        if aggregate_window:
            flux += f'  |> aggregateWindow(every: {aggregate_window}, fn: {aggregate_fn}, createEmpty: false)\n'

        tables = self.query_api.query(query=flux, org=settings.INFLUXDB_ORG)
        results: list[dict[str, Any]] = []
        for table in tables:
            for record in table.records:
                results.append(
                    {
                        "time": record.get_time(),
                        "measurement": record.get_measurement(),
                        "field": record.get_field(),
                        "value": record.get_value(),
                        "data_point_id": record.values.get("data_point_id"),
                        "asset_id": record.values.get("asset_id"),
                        "site_id": record.values.get("site_id"),
                        "quality": record.values.get("quality"),
                    }
                )
        return results

    def get_last_value(self, bucket: str, data_point_id: str) -> dict[str, Any] | None:
        """Get latest value for a datapoint."""
        flux = f'''
from(bucket: "{bucket}")
  |> range(start: -72h)
  |> filter(fn: (r) => r["data_point_id"] == "{data_point_id}")
  |> last()
'''
        tables = self.query_api.query(query=flux, org=settings.INFLUXDB_ORG)
        for table in tables:
            for record in table.records:
                return {
                    "time": record.get_time(),
                    "field": record.get_field(),
                    "value": record.get_value(),
                    "quality": record.values.get("quality"),
                }
        return None

    def check_health(self) -> tuple[bool, str]:
        """Check InfluxDB health quickly."""
        try:
            health = self.client.health()
            if health.status == "pass":
                return True, "ok"
            return False, health.message or "unhealthy"
        except Exception as exc:  # noqa: BLE001
            return False, str(exc)
