"""SQLAlchemy ORM models for ControlTwin."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base declarative class for ORM models."""


class UserRole(str, enum.Enum):
    """User roles."""

    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    OT_ANALYST = "ot_analyst"
    OT_OPERATOR = "ot_operator"
    VIEWER = "viewer"
    READONLY = "readonly"


class Sector(str, enum.Enum):
    """Industry sectors."""

    ELECTRICITY = "electricity"
    OIL = "oil"
    GAS = "gas"
    WATER = "water"
    MANUFACTURING = "manufacturing"
    GENERIC = "generic"


class AssetType(str, enum.Enum):
    """ICS asset types."""

    PLC = "plc"
    RTU = "rtu"
    HMI = "hmi"
    SCADA_SERVER = "scada_server"
    HISTORIAN = "historian"
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    IED = "ied"
    GATEWAY = "gateway"
    SWITCH = "switch"
    TURBINE = "turbine"
    TRANSFORMER = "transformer"
    PUMP = "pump"
    VALVE = "valve"
    METER = "meter"


class ProtocolType(str, enum.Enum):
    """Protocol types for assets and collectors."""

    MODBUS_TCP = "modbus_tcp"
    MODBUS_RTU = "modbus_rtu"
    OPCUA = "opcua"
    DNP3 = "dnp3"
    IEC61850 = "iec61850"
    ICCP = "iccp"
    ETHERNETIP = "ethernetip"
    PROFINET = "profinet"
    BACNET = "bacnet"
    MQTT = "mqtt"
    OTHER = "other"


class Criticality(str, enum.Enum):
    """Asset criticality."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AssetStatus(str, enum.Enum):
    """Asset status values."""

    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    UNKNOWN = "unknown"


class DataType(str, enum.Enum):
    """Data point data types."""

    FLOAT = "float"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    STRING = "string"
    ENUM = "enum"


class AlertSeverity(str, enum.Enum):
    """Alert severities."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertCategory(str, enum.Enum):
    """Alert categories."""

    THRESHOLD_BREACH = "threshold_breach"
    ANOMALY_ML = "anomaly_ml"
    COMMUNICATION_LOSS = "communication_loss"
    UNAUTHORIZED_COMMAND = "unauthorized_command"
    CONFIG_CHANGE = "config_change"
    REPLAY_ATTACK = "replay_attack"
    DOS_ATTEMPT = "dos_attempt"
    RANGE_VIOLATION = "range_violation"
    SEQUENCE_VIOLATION = "sequence_violation"
    MANUAL = "manual"


class AlertStatus(str, enum.Enum):
    """Alert lifecycle statuses."""

    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"


class CollectorProtocol(str, enum.Enum):
    """Collector protocol values."""

    MODBUS_TCP = "modbus_tcp"
    OPCUA = "opcua"
    DNP3 = "dnp3"
    MQTT = "mqtt"
    IEC61850 = "iec61850"


class CollectorStatus(str, enum.Enum):
    """Collector runtime status."""

    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    CONNECTING = "connecting"


class User(Base):
    """User account model."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=UserRole.READONLY,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Site(Base):
    """Industrial site model."""

    __tablename__ = "sites"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sector: Mapped[Sector] = mapped_column(
        Enum(
            Sector,
            name="sector",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=Sector.GENERIC,
    )
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class Asset(Base):
    """ICS asset registry model."""

    __tablename__ = "assets"
    __table_args__ = (UniqueConstraint("site_id", "tag", name="uq_assets_site_tag"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    tag: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    asset_type: Mapped[AssetType] = mapped_column(
        Enum(AssetType, name="asset_type", values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        nullable=False,
    )
    protocol: Mapped[ProtocolType] = mapped_column(
        Enum(ProtocolType, name="protocol_type", values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        nullable=False,
    )
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    port: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    firmware_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    purdue_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    criticality: Mapped[Criticality] = mapped_column(
        Enum(Criticality, name="criticality", values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        nullable=False,
        default=Criticality.MEDIUM,
    )
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="asset_status", values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        nullable=False,
        default=AssetStatus.UNKNOWN,
    )
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    site: Mapped[Site] = relationship()
    parent: Mapped["Asset | None"] = relationship(remote_side=[id])


class DataPoint(Base):
    """Data point metadata model."""

    __tablename__ = "datapoints"
    __table_args__ = (UniqueConstraint("asset_id", "tag", name="uq_datapoints_asset_tag"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    tag: Mapped[str] = mapped_column(String(128), nullable=False)
    data_type: Mapped[DataType] = mapped_column(
        Enum(DataType, name="data_type", values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        nullable=False,
    )
    unit: Mapped[str | None] = mapped_column(String(32), nullable=True)
    engineering_low: Mapped[float | None] = mapped_column(nullable=True)
    engineering_high: Mapped[float | None] = mapped_column(nullable=True)
    alarm_low_low: Mapped[float | None] = mapped_column(nullable=True)
    alarm_low: Mapped[float | None] = mapped_column(nullable=True)
    alarm_high: Mapped[float | None] = mapped_column(nullable=True)
    alarm_high_high: Mapped[float | None] = mapped_column(nullable=True)
    sample_interval_ms: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    is_writable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_updated: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class Alert(Base):
    """Alert model."""

    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("assets.id"), nullable=True)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    severity: Mapped[AlertSeverity] = mapped_column(
        Enum(AlertSeverity, name="alert_severity", values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        nullable=False,
    )
    category: Mapped[AlertCategory] = mapped_column(
        Enum(AlertCategory, name="alert_category", values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        nullable=False,
    )
    mitre_technique_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    mitre_technique_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[AlertStatus] = mapped_column(
        Enum(AlertStatus, name="alert_status", values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        nullable=False,
        default=AlertStatus.OPEN,
    )
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    raw_data: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)


class Collector(Base):
    """Collector model."""

    __tablename__ = "collectors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    protocol: Mapped[CollectorProtocol] = mapped_column(
        Enum(CollectorProtocol, name="collector_protocol", values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        nullable=False,
    )
    host: Mapped[str] = mapped_column(String(255), nullable=False)
    port: Mapped[int] = mapped_column(Integer, nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    poll_interval_ms: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[CollectorStatus] = mapped_column(
        Enum(CollectorStatus, name="collector_status", values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        default=CollectorStatus.STOPPED,
        nullable=False,
    )
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    points_collected_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class SettingScope(str, enum.Enum):
    """Setting scope."""
    GLOBAL = "global"
    USER = "user"
    SITE = "site"


class Setting(Base):
    """Persistent user/site/global setting."""

    __tablename__ = "settings"
    __table_args__ = (UniqueConstraint("key", "scope", "user_id", "site_id", name="uq_settings_key_scope_user_site"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    scope: Mapped[SettingScope] = mapped_column(
        Enum(SettingScope, name="setting_scope", values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        nullable=False,
        default=SettingScope.USER,
    )
    value: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    site_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class AuditLog(Base):
    """Append-only audit log model."""

    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
