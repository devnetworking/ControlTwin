"""Backend unit tests for ControlTwin."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.auth.rbac import Permission, has_permission
from app.collectors.modbus_collector import ModbusTCPCollector
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.models import UserRole
from app.schemas.schemas import AssetCreate, DataPointCreate, UserCreate
from app.services.asset_service import AssetService


def test_password_hash_and_verify() -> None:
    """Hash/verify password."""
    pwd = "SuperStrongPassword123!@#"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_jwt_access_token_create_decode() -> None:
    """Access token should include sub, role, type."""
    token = create_access_token("user-id", "alice", "viewer")
    payload = decode_token(token, expected_type="access")
    assert payload["sub"] == "user-id"
    assert payload["role"] == "viewer"
    assert payload["type"] == "access"
    assert payload["username"] == "alice"


def test_jwt_refresh_token_type() -> None:
    """Refresh token type validation."""
    token = create_refresh_token("user-id", "alice", "viewer")
    payload = decode_token(token, expected_type="refresh")
    assert payload["type"] == "refresh"


def test_invalid_token_raises_401() -> None:
    """Invalid token raises HTTP 401."""
    with pytest.raises(HTTPException) as exc:
        decode_token("invalid-token")
    assert exc.value.status_code == 401


def test_rbac_viewer_read_assets_not_create() -> None:
    """Viewer can read assets but not create."""
    assert has_permission(UserRole.VIEWER, Permission.ASSET_READ) is True
    assert has_permission(UserRole.VIEWER, Permission.ASSET_CREATE) is False


def test_rbac_ot_operator_ack_not_manage() -> None:
    """OT operator can acknowledge alerts but not manage."""
    assert has_permission(UserRole.OT_OPERATOR, Permission.ALERT_ACKNOWLEDGE) is True
    assert has_permission(UserRole.OT_OPERATOR, Permission.ALERT_MANAGE) is False


def test_rbac_super_admin_all_permissions() -> None:
    """Super admin has all permissions."""
    for perm in Permission:
        assert has_permission(UserRole.SUPER_ADMIN, perm) is True


def test_rbac_readonly_min_permissions() -> None:
    """Readonly has only minimal permissions."""
    assert has_permission(UserRole.READONLY, Permission.ASSET_READ) is True
    assert has_permission(UserRole.READONLY, Permission.DATAPOINT_READ) is True
    assert has_permission(UserRole.READONLY, Permission.ALERT_READ) is False


@pytest.mark.asyncio
async def test_asset_service_get_or_404_raises() -> None:
    """AssetService.get_or_404 raises 404 when asset not found."""
    session = AsyncMock()
    execute_result = MagicMock()
    execute_result.scalar_one_or_none.return_value = None
    session.execute = AsyncMock(return_value=execute_result)
    service = AssetService(session=session)
    with pytest.raises(HTTPException) as exc:
        await service.get_or_404(uuid.uuid4())
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_asset_service_create_asset_duplicate_tag_raises_409() -> None:
    """AssetService.create_asset raises 409 on duplicate tag."""
    session = AsyncMock()
    duplicate_result = MagicMock()
    duplicate_result.scalar_one_or_none.return_value = object()
    session.execute.return_value = duplicate_result

    service = AssetService(session=session)
    payload = AssetCreate(
        site_id=uuid.uuid4(),
        parent_id=None,
        name="Pump 1",
        tag="PUMP_001",
        description="Main pump",
        asset_type="pump",
        protocol="modbus_tcp",
        ip_address="10.0.0.10",
        port=502,
        vendor="Vendor",
        model="Model",
        firmware_version="1.0",
        purdue_level=1,
        criticality="high",
        status="online",
        metadata={},
    )
    with pytest.raises(HTTPException) as exc:
        await service.create_asset(payload)
    assert exc.value.status_code == 409


def test_asset_tag_regex_validation_invalid() -> None:
    """Asset tag with spaces/special chars should fail."""
    with pytest.raises(ValidationError):
        AssetCreate(
            site_id=uuid.uuid4(),
            parent_id=None,
            name="Pump 1",
            tag="BAD TAG !",
            description="Main pump",
            asset_type="pump",
            protocol="modbus_tcp",
            ip_address="10.0.0.10",
            port=502,
            vendor="Vendor",
            model="Model",
            firmware_version="1.0",
            purdue_level=1,
            criticality="high",
            status="online",
            metadata={},
        )


def test_asset_port_range_validation_invalid() -> None:
    """Asset port > 65535 should fail."""
    with pytest.raises(ValidationError):
        AssetCreate(
            site_id=uuid.uuid4(),
            parent_id=None,
            name="Pump 1",
            tag="PUMP_001",
            description="Main pump",
            asset_type="pump",
            protocol="modbus_tcp",
            ip_address="10.0.0.10",
            port=70000,
            vendor="Vendor",
            model="Model",
            firmware_version="1.0",
            purdue_level=1,
            criticality="high",
            status="online",
            metadata={},
        )


def test_datapoint_is_writable_defaults_false() -> None:
    """DataPoint is_writable default should be false."""
    payload = DataPointCreate(
        asset_id=uuid.uuid4(),
        name="Pressure",
        tag="PRESSURE_01",
        data_type="float",
        unit="bar",
        sample_interval_ms=1000,
        metadata={},
    )
    assert payload.is_writable is False


def test_usercreate_invalid_role_raises() -> None:
    """UserCreate should reject invalid role."""
    with pytest.raises(ValidationError):
        UserCreate(
            username="john",
            email="john@example.com",
            password="VeryStrongPassword123!",
            role="invalid_role",
        )


def test_modbus_read_functions_no_write_functions() -> None:
    """Security check: no write FC methods in READ_FUNCTIONS."""
    forbidden = {"write_coil", "write_register", "write_coils", "write_registers"}
    methods = set(ModbusTCPCollector.READ_FUNCTIONS.values())
    assert methods.isdisjoint(forbidden)
