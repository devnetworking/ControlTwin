"""Kafka producer service for ControlTwin event streaming."""

from __future__ import annotations

import json
import logging
from typing import Any

from aiokafka import AIOKafkaProducer

from app.core.config import settings

logger = logging.getLogger(__name__)


class KafkaProducerService:
    """Async Kafka producer with graceful degradation."""

    def __init__(self) -> None:
        self.producer: AIOKafkaProducer | None = None
        self.started = False

    async def start(self) -> None:
        """Start Kafka producer."""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                acks="all",
                compression_type="gzip",
                enable_idempotence=True,
                value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
                key_serializer=lambda v: v.encode("utf-8") if isinstance(v, str) else v,
            )
            await self.producer.start()
            self.started = True
            logger.info("Kafka producer started")
        except Exception as exc:  # noqa: BLE001
            self.producer = None
            self.started = False
            logger.warning("Kafka unavailable, continuing without producer: %s", exc)

    async def stop(self) -> None:
        """Stop Kafka producer."""
        if self.producer:
            await self.producer.stop()
            logger.info("Kafka producer stopped")
        self.started = False

    async def publish_datapoint(self, asset_id: str, payload: dict[str, Any]) -> None:
        """Publish datapoint event."""
        await self._publish(settings.KAFKA_TOPIC_DATAPOINTS, asset_id, payload)

    async def publish_alert(self, site_id: str, payload: dict[str, Any]) -> None:
        """Publish alert event."""
        await self._publish(settings.KAFKA_TOPIC_ALERTS, site_id, payload)

    async def publish_event(self, payload: dict[str, Any], key: str = "event") -> None:
        """Publish generic event."""
        await self._publish(settings.KAFKA_TOPIC_EVENTS, key, payload)

    async def _publish(self, topic: str, key: str, payload: dict[str, Any]) -> None:
        """Internal safe publish helper."""
        if not self.producer or not self.started:
            logger.warning("Kafka producer not available; skipped publish topic=%s", topic)
            return
        try:
            await self.producer.send_and_wait(topic, key=key, value=payload)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Kafka publish failed topic=%s error=%s", topic, exc)
