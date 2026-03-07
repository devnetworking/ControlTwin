from __future__ import annotations

import asyncio
import json
from typing import Any

import redis.asyncio as redis
from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from app.anomaly.detector import AnomalyDetector
from app.core.config import get_settings
from app.core.logging import get_logger
from app.twin_state.engine import TwinStateEngine


class ICSDataConsumer:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.logger = get_logger("controltwin-ai.kafka-consumer")
        self.consumer = AIOKafkaConsumer(
            self.settings.kafka_topic_datapoints,
            bootstrap_servers=self.settings.kafka_bootstrap_servers,
            group_id="controltwin-ai",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        self.redis = redis.from_url(self.settings.redis_url, decode_responses=True)
        self.twin = TwinStateEngine()
        self.detector = AnomalyDetector()

    async def start(self) -> None:
        await self.consumer.start()
        await self.producer.start()
        await self.twin.init_db()
        self.logger.info("kafka consumer started", extra={"event": "consumer_start"})
        try:
            async for msg in self.consumer:
                await self.process_message(msg.value)
        finally:
            await self.consumer.stop()
            await self.producer.stop()
            await self.redis.close()

    async def process_message(self, message: dict[str, Any]) -> None:
        asset_id = str(message.get("asset_id", ""))
        data_point_id = str(message.get("data_point_id", ""))
        tag = str(message.get("tag", data_point_id))
        value = float(message.get("value", 0.0))
        timestamp = message.get("timestamp")
        quality = message.get("quality", "good")
        asset_type = message.get("asset_type", "default")

        if not asset_id or not data_point_id:
            return

        await self.twin.update_reported(asset_id=asset_id, data_point_tag=tag, value=value, timestamp=timestamp, quality=quality)

        det = await self.detector.process_datapoint({
            "asset_id": asset_id,
            "data_point_id": data_point_id,
            "tag": tag,
            "value": value,
            "timestamp": timestamp,
            "quality": quality,
            "asset_type": asset_type,
            "alarm_low_low": message.get("alarm_low_low"),
            "alarm_low": message.get("alarm_low"),
            "alarm_high": message.get("alarm_high"),
            "alarm_high_high": message.get("alarm_high_high"),
        })

        await self.redis.rpush(f"features:{data_point_id}", value)
        await self.redis.ltrim(f"features:{data_point_id}", -60, -1)

        if det.get("is_anomaly"):
            await self.producer.send_and_wait(
                self.settings.kafka_topic_alerts,
                {
                    "source": "controltwin-ai",
                    "asset_id": asset_id,
                    "data_point_id": data_point_id,
                    "final_score": det.get("final_score"),
                    "mitre_technique_id": det.get("mitre_technique", {}).get("id"),
                    "timestamp": timestamp,
                },
            )


async def main() -> None:
    consumer = ICSDataConsumer()
    await consumer.start()


if __name__ == "__main__":
    asyncio.run(main())
