"""Configuration settings for the ControlTwin AI microservice."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    OLLAMA_URL: str = "http://localhost:11434"
    CHROMADB_URL: str = "http://localhost:8010"
    REDIS_URL: str = "redis://localhost:6379"
    MLFLOW_URL: str = "http://localhost:5000"
    BACKEND_URL: str = "http://localhost:8000"

    MODEL_PRIMARY: str = "mistral:7b"
    MODEL_EMBED: str = "nomic-embed-text"

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_TOPIC_DATAPOINTS: str = "ics.datapoints"
    KAFKA_TOPIC_ALERTS: str = "ics.alerts"

    LOG_LEVEL: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object."""
    return Settings()
