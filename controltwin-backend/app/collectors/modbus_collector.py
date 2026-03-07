"""Secure read-only Modbus TCP collector for ControlTwin."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pymodbus.client import AsyncModbusTcpClient

from app.db.influxdb import InfluxRepository
from app.services.kafka_service import KafkaProducerService

logger = logging.getLogger(__name__)


@dataclass
class DataPointConfig:
    """Configuration for a Modbus datapoint."""

    data_point_id: str
    site_id: str
    asset_id: str
    tag: str
    register_type: str
    address: int
    count: int = 1
    slave: int = 1
    scale_factor: float = 1.0
    offset: float = 0.0


class ModbusTCPCollector:
    """Read-only Modbus collector using FC01/02/03/04 only."""

    READ_FUNCTIONS = {
        "coil": "read_coils",  # FC01
        "discrete_input": "read_discrete_inputs",  # FC02
        "holding": "read_holding_registers",  # FC03 (read-only usage)
        "input": "read_input_registers",  # FC04
    }

    def __init__(
        self,
        host: str,
        port: int,
        points: list[DataPointConfig],
        influx: InfluxRepository,
        kafka: KafkaProducerService,
        poll_interval_ms: int = 1000,
        retries: int = 5,
    ) -> None:
        self.host = host
        self.port = port
        self.points = points
        self.influx = influx
        self.kafka = kafka
        self.poll_interval_ms = poll_interval_ms
        self.retries = retries
        self._running = False
        self.client: AsyncModbusTcpClient | None = None

    async def connect(self) -> bool:
        """Connect with retry logic."""
        for attempt in range(1, self.retries + 1):
            try:
                self.client = AsyncModbusTcpClient(host=self.host, port=self.port)
                connected = await self.client.connect()
                if connected:
                    logger.info("Modbus collector connected host=%s port=%s", self.host, self.port)
                    return True
            except Exception as exc:  # noqa: BLE001
                logger.warning("Modbus connect attempt=%s failed error=%s", attempt, exc)
            await asyncio.sleep(min(2 * attempt, 10))
        return False

    async def close(self) -> None:
        """Close modbus client."""
        if self.client:
            self.client.close()

    async def _read_point(self, point: DataPointConfig) -> tuple[Any | None, str]:
        """Read a datapoint from Modbus using read-only functions only."""
        if not self.client:
            return None, "bad"

        fn_name = self.READ_FUNCTIONS.get(point.register_type)
        if not fn_name:
            logger.error("Invalid register type=%s for datapoint=%s", point.register_type, point.data_point_id)
            return None, "bad"

        try:
            fn = getattr(self.client, fn_name)
            response = await fn(address=point.address, count=point.count, slave=point.slave)
            if response.isError():
                return None, "bad"

            if point.register_type in {"coil", "discrete_input"}:
                raw = response.bits[0] if response.bits else False
                value = bool(raw)
            else:
                raw = response.registers[0] if response.registers else 0
                value = float(raw) * point.scale_factor + point.offset
            return value, "good"
        except Exception as exc:  # noqa: BLE001
            logger.warning("Modbus read error datapoint=%s error=%s", point.data_point_id, exc)
            return None, "bad"

    async def _emit(self, point: DataPointConfig, value: Any | None, quality: str) -> None:
        """Emit value to InfluxDB and Kafka."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "site_id": point.site_id,
            "asset_id": point.asset_id,
            "data_point_id": point.data_point_id,
            "tag": point.tag,
            "value": value,
            "quality": quality,
            "protocol": "modbus_tcp",
        }
        if value is not None:
            self.influx.write_measurement(
                bucket=self.influx.realtime_bucket,
                measurement="ics_datapoint",
                site_id=point.site_id,
                asset_id=point.asset_id,
                data_point_id=point.data_point_id,
                tag=point.tag,
                quality=quality,
                value=value,
                timestamp_ms=int(datetime.now(timezone.utc).timestamp() * 1000),
            )
        await self.kafka.publish_datapoint(point.asset_id, payload)

    async def run(self) -> None:
        """Run polling loop."""
        self._running = True
        if not await self.connect():
            logger.error("Modbus collector failed to connect")
            return

        try:
            while self._running:
                for point in self.points:
                    value, quality = await self._read_point(point)
                    await self._emit(point, value, quality)
                await asyncio.sleep(self.poll_interval_ms / 1000.0)
        finally:
            await self.close()

    def stop(self) -> None:
        """Stop run loop."""
        self._running = False
