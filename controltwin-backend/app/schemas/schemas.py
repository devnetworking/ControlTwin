"""Pydantic v2 schemas for ControlTwin API."""

from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.models import (
    AlertCategory,
    AlertSeverity,
    AlertStatus,
    AssetStatus,
    AssetType,
    CollectorProtocol,
    CollectorStatus,
    Criticality,
    DataType,
    ProtocolType,
    Sector,
    UserRole,
)
import enum

ASSET_TAG_REGEX = re.compile(r"^[A-Za-z0-9_\-\.]+$")


class TokenResponse(BaseModel):
    """JWT token response schema."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    role: UserRole


class LoginRequest(BaseModel):
    """Login request payload."""

    model_config = ConfigDict(from_attributes=True)

    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    """Refresh token request payload."""

    model_config = ConfigDict(from_attributes=True)

    refresh_token: str


class UserBase(BaseModel):
    """Common user fields."""

    model_config = ConfigDict(from_attributes=True)

    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    role: UserRole


class UserCreate(UserBase):
    """User creation schema."""

    password: str = Field(min_length=12, max_length=128)


class UserUpdate(BaseModel):
    """User partial update schema."""

    model_config = ConfigDict(from_attributes=True)

    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(UserBase):
    """User response schema."""

    id: uuid.UUID
    is_active: bool
    failed_login_attempts: int
    locked_until: datetime | None = None
    last_login: datetime | None = None
    created_at: datetime
    updated_at: datetime


class SiteBase(BaseModel):
    """Common site fields."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(min_length=2, max_length=128)
    description: str | None = None
    location: str | None = None
    sector: Sector = Sector.GENERIC
    timezone: str = "UTC"
    metadata: dict[str, Any] = Field(default_factory=dict)


class SiteCreate(SiteBase):
    """Site creation schema."""


class SiteUpdate(BaseModel):
    """Site update schema (partial)."""

    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(default=None, min_length=2, max_length=128)
    description: str | None = None
    location: str | None = None
    sector: Sector | None = None
    timezone: str | None = None
    metadata: dict[str, Any] | None = None
    is_active: bool | None = None


class SiteResponse(SiteBase):
    """Site response schema."""

    id: uuid.UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AssetBase(BaseModel):
    """Common asset fields."""

    model_config = ConfigDict(from_attributes=True)

    site_id: uuid.UUID
    parent_id: uuid.UUID | None = None
    name: str = Field(min_length=2, max_length=128)
    tag: str = Field(min_length=1, max_length=128)
    description: str | None = None
    asset_type: AssetType
    protocol: ProtocolType
    ip_address: str | None = None
    port: int | None = None
    vendor: str | None = None
    model: str | None = None
    firmware_version: str | None = None
    purdue_level: int | None = Field(default=None, ge=0, le=4)
    criticality: Criticality = Criticality.MEDIUM
    status: AssetStatus = AssetStatus.UNKNOWN
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("tag")
    @classmethod
    def validate_tag(cls, value: str) -> str:
        """Validate asset tag format."""
        if not ASSET_TAG_REGEX.match(value):
            raise ValueError("Asset tag may only contain letters, numbers, underscore, hyphen, dot")
        return value

    @field_validator("port")
    @classmethod
    def validate_port(cls, value: int | None) -> int | None:
        """Validate TCP/UDP port range."""
        if value is None:
            return value
        if not (1 <= value <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return value


class AssetCreate(AssetBase):
    """Asset creation schema."""


class AssetUpdate(BaseModel):
    """Asset patch schema."""

    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(default=None, min_length=2, max_length=128)
    description: str | None = None
    status: AssetStatus | None = None
    criticality: Criticality | None = None
    metadata: dict[str, Any] | None = None
    ip_address: str | None = None
    port: int | None = None

    @field_validator("port")
    @classmethod
    def validate_port(cls, value: int | None) -> int | None:
        """Validate TCP/UDP port range for updates."""
        if value is None:
            return value
        if not (1 <= value <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return value


class AssetResponse(AssetBase):
    """Asset response schema."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    is_active: bool
    last_seen: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DataPointBase(BaseModel):
    """Common datapoint fields."""

    model_config = ConfigDict(from_attributes=True)

    asset_id: uuid.UUID
    name: str = Field(min_length=1, max_length=128)
    tag: str = Field(min_length=1, max_length=128)
    data_type: DataType
    unit: str | None = None
    engineering_low: float | None = None
    engineering_high: float | None = None
    alarm_low_low: float | None = None
    alarm_low: float | None = None
    alarm_high: float | None = None
    alarm_high_high: float | None = None
    sample_interval_ms: int = Field(default=1000, ge=100)
    metadata: dict[str, Any] = Field(default_factory=dict)


class DataPointCreate(DataPointBase):
    """DataPoint creation schema."""

    is_writable: bool = False


class DataPointResponse(DataPointBase):
    """DataPoint response schema."""

    id: uuid.UUID
    is_writable: bool = False
    last_value: str | None = None
    last_updated: datetime | None = None
    created_at: datetime


class DataPointQueryRequest(BaseModel):
    """Influx query request for datapoints."""

    model_config = ConfigDict(from_attributes=True)

    data_point_ids: list[uuid.UUID]
    start: datetime
    stop: datetime
    aggregate_window: str | None = None
    aggregate_fn: str = "mean"


class AlertBase(BaseModel):
    """Common alert fields."""

    model_config = ConfigDict(from_attributes=True)

    asset_id: uuid.UUID | None = None
    site_id: uuid.UUID
    title: str = Field(min_length=3, max_length=255)
    description: str | None = None
    severity: AlertSeverity
    category: AlertCategory
    mitre_technique_id: str | None = None
    mitre_technique_name: str | None = None
    raw_data: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AlertCreate(AlertBase):
    """Alert creation schema."""


class AlertResponse(AlertBase):
    """Alert response schema."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    status: AlertStatus
    triggered_at: datetime
    acknowledged_at: datetime | None = None
    resolved_at: datetime | None = None
    acknowledged_by: uuid.UUID | None = None


class AlertAcknowledgeRequest(BaseModel):
    """Alert acknowledge payload."""

    model_config = ConfigDict(from_attributes=True)

    comment: str | None = None


class AlertResolveRequest(BaseModel):
    """Alert resolve payload."""

    model_config = ConfigDict(from_attributes=True)

    resolution_note: str | None = None
    is_false_positive: bool = False


class CollectorBase(BaseModel):
    """Common collector fields."""

    model_config = ConfigDict(from_attributes=True)

    site_id: uuid.UUID
    name: str = Field(min_length=2, max_length=128)
    protocol: CollectorProtocol
    host: str
    port: int = Field(ge=1, le=65535)
    config: dict[str, Any] = Field(default_factory=dict)
    poll_interval_ms: int = Field(default=1000, ge=100)
    is_active: bool = True


class CollectorCreate(CollectorBase):
    """Collector creation schema."""


class CollectorResponse(CollectorBase):
    """Collector response schema."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    status: CollectorStatus
    last_heartbeat: datetime | None = None
    last_error: str | None = None
    points_collected_total: int
    created_at: datetime
    updated_at: datetime


class HealthComponent(BaseModel):
    """Health component state."""

    model_config = ConfigDict(from_attributes=True)

    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    """System health response."""

    model_config = ConfigDict(from_attributes=True)

    status: str
    components: dict[str, HealthComponent]


class SettingScope(str, enum.Enum):
    GLOBAL = "global"
    USER = "user"
    SITE = "site"


class SettingUpsertRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scope: SettingScope = SettingScope.USER
    user_id: uuid.UUID | None = None
    site_id: uuid.UUID | None = None
    value: dict[str, Any] = Field(default_factory=dict)


class SettingsBulkItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str = Field(min_length=1, max_length=128)
    scope: SettingScope = SettingScope.USER
    user_id: uuid.UUID | None = None
    site_id: uuid.UUID | None = None
    value: dict[str, Any] = Field(default_factory=dict)


class SettingsBulkUpsertRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    items: list[SettingsBulkItem] = Field(default_factory=list)


class SettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    scope: SettingScope
    value: dict[str, Any]
    user_id: uuid.UUID | None = None
    site_id: uuid.UUID | None = None
    updated_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
