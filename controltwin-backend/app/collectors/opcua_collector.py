"""Read-only OPC-UA subscription collector for ControlTwin."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from asyncua import Client

from app.db.influxdb import InfluxRepository
from app.services.kafka_service import KafkaProducerService

logger = logging.getLogger(__name__)


@dataclass
class OPCUADataPointConfig:
    """OPC-UA datapoint mapping."""

    node_id: str
    data_point_id: str
    site_id: str
    asset_id: str
    tag: str


class _SubscriptionHandler:
    """Internal handler for OPC-UA data change notifications."""

    def __init__(self, collector: "OPCUACollector") -> None:
        self.collector = collector

    async def datachange_notification(self, node: Any, val: Any, data: Any) -> None:
        """Handle server-pushed data changes."""
        node_id = node.nodeid.to_string()
        cfg = self.collector.node_map.get(node_id)
        if not cfg:
            return

        quality = "good"
        try:
            status_code = str(data.monitored_item.Value.StatusCode)
            if "Uncertain" in status_code:
                quality = "uncertain"
            elif "Bad" in status_code:
                quality = "bad"
        except Exception:  # noqa: BLE001
            quality = "uncertain"

        timestamp_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
        self.collector.influx.write_measurement(
            bucket=self.collector.influx.realtime_bucket,
            measurement="ics_datapoint",
            site_id=cfg.site_id,
            asset_id=cfg.asset_id,
            data_point_id=cfg.data_point_id,
            tag=cfg.tag,
            quality=quality,
            value=val,
            timestamp_ms=timestamp_ms,
        )

        await self.collector.kafka.publish_datapoint(
            cfg.asset_id,
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "protocol": "opcua",
                "site_id": cfg.site_id,
                "asset_id": cfg.asset_id,
                "data_point_id": cfg.data_point_id,
                "tag": cfg.tag,
                "value": val,
                "quality": quality,
            },
        )


class OPCUACollector:
    """Subscription-based read-only OPC-UA collector."""

    def __init__(
        self,
        endpoint: str,
        points: list[OPCUADataPointConfig],
        influx: InfluxRepository,
        kafka: KafkaProducerService,
        username: str | None = None,
        password: str | None = None,
        cert_path: str | None = None,
        private_key_path: str | None = None,
        keepalive_seconds: int = 10,
        reconnect_delay_seconds: int = 5,
    ) -> None:
        self.endpoint = endpoint
        self.points = points
        self.node_map = {p.node_id: p for p in points}
        self.influx = influx
        self.kafka = kafka
        self.username = username
        self.password = password
        self.cert_path = cert_path
        self.private_key_path = private_key_path
        self.keepalive_seconds = keepalive_seconds
        self.reconnect_delay_seconds = reconnect_delay_seconds
        self._running = False

    async def _build_client(self) -> Client:
        """Configure OPC-UA client auth options."""
        client = Client(url=self.endpoint)
        if self.username and self.password:
            client.set_user(self.username)
            client.set_password(self.password)
        if self.cert_path and self.private_key_path:
            await client.set_security_string(
                f"Basic256Sha256,SignAndEncrypt,{self.cert_path},{self.private_key_path}"
            )
        return client

    async def run(self) -> None:
        """Run reconnect loop with subscription keep-alive."""
        self._running = True
        while self._running:
            client: Client | None = None
            try:
                client = await self._build_client()
                await client.connect()
                logger.info("OPC-UA collector connected endpoint=%s", self.endpoint)

                handler = _SubscriptionHandler(self)
                subscription = await client.create_subscription(self.keepalive_seconds * 1000, handler)

                for point in self.points:
                    node = client.get_node(point.node_id)
                    await subscription.subscribe_data_change(node)

                while self._running:
                    await asyncio.sleep(self.keepalive_seconds)
            except Exception as exc:  # noqa: BLE001
                logger.warning("OPC-UA collector error endpoint=%s error=%s", self.endpoint, exc)
                await asyncio.sleep(self.reconnect_delay_seconds)
            finally:
                if client:
                    try:
                        await client.disconnect()
                    except Exception:  # noqa: BLE001
                        pass

    def stop(self) -> None:
        """Stop collector loop."""
        self._running = False
