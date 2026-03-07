from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    controltwin_ai_host: str = "0.0.0.0"
    controltwin_ai_port: int = 8001
    backend_base_url: str = "http://localhost:8000/api/v1"

    postgres_dsn: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/controltwin"
    influx_url: str = "http://localhost:8086"
    influx_token: str = "controltwin-token"
    influx_org: str = "controltwin"
    influx_bucket: str = "ics_realtime"
    influx_anomaly_bucket: str = "ics_anomaly_scores"

    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic_datapoints: str = "ics.datapoints"
    kafka_topic_alerts: str = "ics.alerts"
    kafka_group_id: str = "controltwin-ai"

    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://redis:6379/0"
    celery_result_backend: str = "redis://redis:6379/1"

    ollama_base_url: str = "http://localhost:11434"
    ollama_model_mistral: str = "mistral:7b"
    ollama_model_embed: str = "nomic-embed-text"
    ollama_model_fallback: str = "llama3.2:3b"

    chroma_persist_dir: str = "./chroma_data"
    chroma_collection: str = "controltwin_ics_kb"

    mlflow_tracking_uri: str = "http://localhost:5000"
    model_dir: str = "./models"

    divergence_threshold_pct: float = 5.0
    divergence_critical_minutes: int = 15
    anomaly_final_threshold: float = 0.7
    anomaly_iso_contamination: float = 0.05
    lstm_default_threshold: float = 0.15

    log_level: str = "INFO"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
