"""Async Kafka consumer for datapoints ingestion and anomaly alert publishing."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer
import structlog

from app.anomaly.detector import AnomalyDetector
from app.core.config import get_settings
from app.twin_state.engine import DigitalTwinEngine


class KafkaDatapointConsumer:
    """Consumes datapoints, updates digital twin, detects anomalies, and publishes alerts."""

    def __init__(self) -> None:
        """Initialize Kafka consumer/producer and service engines."""
        self.settings = get_settings()
        self.logger = structlog.get_logger("controltwin-ai.kafka")
        self.twin_engine = DigitalTwinEngine()
        self.anomaly_detector = AnomalyDetector()

        self.consumer = AIOKafkaConsumer(
            self.settings.KAFKA_TOPIC_DATAPOINTS,
            bootstrap_servers=self.settings.KAFKA_BOOTSTRAP_SERVERS,
            value_deserializer=lambda v: json.loads(v.decode("utf-8")),
            group_id="controltwin-ai-consumer",
            auto_offset_reset="latest",
            enable_auto_commit=True,
        )
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )

    async def start(self) -> None:
        """Start consuming datapoints indefinitely."""
        await self.consumer.start()
        await self.producer.start()
        self.logger.info("kafka_consumer_started", topic=self.settings.KAFKA_TOPIC_DATAPOINTS)

        try:
            async for message in self.consumer:
                await self._handle_message(message.value)
        except Exception as exc:
            self.logger.error("kafka_consumer_failed", error=str(exc))
        finally:
            await self.consumer.stop()
            await self.producer.stop()
            self.logger.info("kafka_consumer_stopped")

    async def _handle_message(self, payload: dict[str, Any]) -> None:
        """Process one datapoint payload."""
        try:
            asset_id = str(payload.get("asset_id", ""))
            if not asset_id:
                return

            datapoint = {
                "tag": payload.get("tag", payload.get("data_point_id", "unknown")),
                "value": payload.get("value", 0.0),
                "timestamp": payload.get("timestamp"),
                "quality": payload.get("quality", "good"),
            }

            await self.twin_engine.sync_asset(asset_id=asset_id, datapoints=[datapoint])
            result = await self.anomaly_detector.detect(asset_id=asset_id, datapoints=[datapoint])

            if result.is_anomaly:
                alert_payload = {
                    "asset_id": asset_id,
                    "source": "controltwin-ai",
                    "score": result.score,
                    "confidence": result.confidence,
                    "mitre_technique": result.technique,
                    "message": "Anomaly detected from streaming datapoint.",
                }
                await self.producer.send_and_wait(self.settings.KAFKA_TOPIC_ALERTS, alert_payload)
                self.logger.info("anomaly_alert_published", asset_id=asset_id, technique=result.technique)
        except Exception as exc:
            self.logger.error("kafka_message_processing_failed", error=str(exc), payload=payload)


async def main() -> None:
    """Run the Kafka datapoint consumer."""
    consumer = KafkaDatapointConsumer()
    await consumer.start()


if __name__ == "__main__":
    asyncio.run(main())
