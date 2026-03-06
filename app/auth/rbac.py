"""Role-based access control for ControlTwin."""

from __future__ import annotations

import enum
from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.models.models import User, UserRole


class Permission(str, enum.Enum):
    """Supported RBAC permissions."""

    ASSET_READ = "asset:read"
    ASSET_CREATE = "asset:create"
    ASSET_UPDATE = "asset:update"
    ASSET_DELETE = "asset:delete"
    DATAPOINT_READ = "datapoint:read"
    DATAPOINT_WRITE = "datapoint:write"
    ALERT_READ = "alert:read"
    ALERT_ACKNOWLEDGE = "alert:acknowledge"
    ALERT_MANAGE = "alert:manage"
    COLLECTOR_READ = "collector:read"
    COLLECTOR_MANAGE = "collector:manage"
    REPORT_READ = "report:read"
    REPORT_GENERATE = "report:generate"
    AUDIT_READ = "audit:read"
    USER_READ = "user:read"
    USER_MANAGE = "user:manage"


ROLE_PERMISSIONS: dict[UserRole, set[Permission]] = {
    UserRole.READONLY: {
        Permission.ASSET_READ,
        Permission.DATAPOINT_READ,
    },
    UserRole.VIEWER: {
        Permission.ASSET_READ,
        Permission.DATAPOINT_READ,
        Permission.ALERT_READ,
        Permission.REPORT_READ,
    },
    UserRole.OT_OPERATOR: {
        Permission.ASSET_READ,
        Permission.DATAPOINT_READ,
        Permission.ALERT_READ,
        Permission.REPORT_READ,
        Permission.ALERT_ACKNOWLEDGE,
        Permission.COLLECTOR_READ,
    },
    UserRole.OT_ANALYST: {
        Permission.ASSET_READ,
        Permission.DATAPOINT_READ,
        Permission.ALERT_READ,
        Permission.REPORT_READ,
        Permission.ALERT_ACKNOWLEDGE,
        Permission.COLLECTOR_READ,
        Permission.ASSET_CREATE,
        Permission.ASSET_UPDATE,
        Permission.DATAPOINT_WRITE,
        Permission.ALERT_MANAGE,
        Permission.COLLECTOR_MANAGE,
        Permission.REPORT_GENERATE,
        Permission.AUDIT_READ,
    },
    UserRole.ADMIN: {
        Permission.ASSET_READ,
        Permission.DATAPOINT_READ,
        Permission.ALERT_READ,
        Permission.REPORT_READ,
        Permission.ALERT_ACKNOWLEDGE,
        Permission.COLLECTOR_READ,
        Permission.ASSET_CREATE,
        Permission.ASSET_UPDATE,
        Permission.DATAPOINT_WRITE,
        Permission.ALERT_MANAGE,
        Permission.COLLECTOR_MANAGE,
        Permission.REPORT_GENERATE,
        Permission.AUDIT_READ,
        Permission.ASSET_DELETE,
        Permission.USER_READ,
        Permission.USER_MANAGE,
    },
    UserRole.SUPER_ADMIN: set(Permission),
}


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Check if role has a specific permission."""
    if role == UserRole.SUPER_ADMIN:
        return True
    return permission in ROLE_PERMISSIONS.get(role, set())


def require_permission(permission: Permission) -> Callable[[User], User]:
    """FastAPI dependency that enforces a permission."""

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if not has_permission(current_user.role, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permission: {permission.value}",
            )
        return current_user

    return _checker


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """FastAPI dependency that enforces one of allowed roles."""

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles and current_user.role != UserRole.SUPER_ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return current_user

    return _checker
