"""Application configuration settings loaded via pydantic-settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings for ControlTwin."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "ControlTwin"
    APP_ENV: str = Field(default="development")
    APP_DEBUG: bool = Field(default=True)
    APP_HOST: str = Field(default="0.0.0.0")
    APP_PORT: int = Field(default=8000)
    API_V1_PREFIX: str = Field(default="/api/v1")

    JWT_SECRET_KEY: str = Field(default="change_me_super_secret")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7)

    PASSWORD_BCRYPT_ROUNDS: int = Field(default=12)
    MAX_FAILED_LOGIN_ATTEMPTS: int = Field(default=5)
    ACCOUNT_LOCK_MINUTES: int = Field(default=15)

    POSTGRES_HOST: str = Field(default="postgres")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_DB: str = Field(default="controltwin")
    POSTGRES_USER: str = Field(default="controltwin")
    POSTGRES_PASSWORD: str = Field(default="controltwin")

    INFLUXDB_URL: str = Field(default="http://influxdb:8086")
    INFLUXDB_TOKEN: str = Field(default="controltwin-influx-token")
    INFLUXDB_ORG: str = Field(default="controltwin")
    INFLUXDB_BUCKET_REALTIME: str = Field(default="ics_realtime")
    INFLUXDB_BUCKET_HISTORY: str = Field(default="ics_history")

    KAFKA_BOOTSTRAP_SERVERS: str = Field(default="kafka:9092")
    KAFKA_TOPIC_DATAPOINTS: str = Field(default="ics.datapoints")
    KAFKA_TOPIC_ALERTS: str = Field(default="ics.alerts")
    KAFKA_TOPIC_EVENTS: str = Field(default="ics.events")

    MQTT_BROKER_HOST: str = Field(default="mqtt")
    MQTT_BROKER_PORT: int = Field(default=1883)
    MQTT_USERNAME: str | None = None
    MQTT_PASSWORD: str | None = None

    REDIS_URL: str = Field(default="redis://redis:6379/0")

    PGADMIN_DEFAULT_EMAIL: str = Field(default="admin@controltwin.local")
    PGADMIN_DEFAULT_PASSWORD: str = Field(default="admin")


settings = Settings()


def get_postgres_dsn() -> str:
    """Build async SQLAlchemy PostgreSQL DSN."""
    return (
        f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
    )
