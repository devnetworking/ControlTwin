from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.db.postgres import get_session
from app.models.models import Setting, SettingScope as SettingScopeModel, User
from app.schemas.schemas import (
    SettingsBulkUpsertRequest,
    SettingResponse,
    SettingScope,
    SettingUpsertRequest,
)

router = APIRouter(prefix="/settings", tags=["settings"])


def _is_admin(user: User) -> bool:
    return user.role.value in {"admin", "super_admin"}


def _validate_scope_access(
    scope: SettingScope,
    current_user: User,
    user_id: uuid.UUID | None,
) -> None:
    if scope == SettingScope.GLOBAL and not _is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Global settings require admin role")
    if scope == SettingScope.USER and user_id and user_id != current_user.id and not _is_admin(current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify another user's settings")


def _to_response(row: Setting) -> SettingResponse:
    return SettingResponse(
        id=row.id,
        key=row.key,
        scope=SettingScope(row.scope.value),
        value=row.value,
        user_id=row.user_id,
        site_id=row.site_id,
        updated_by=row.updated_by,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


@router.get("", response_model=list[SettingResponse])
async def list_settings(
    scope: SettingScope | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    site_id: uuid.UUID | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[SettingResponse]:
    query = select(Setting)

    if scope is not None:
        query = query.where(Setting.scope == SettingScopeModel(scope.value))
    if user_id is not None:
        query = query.where(Setting.user_id == user_id)
    if site_id is not None:
        query = query.where(Setting.site_id == site_id)

    if not _is_admin(current_user):
        query = query.where(
            (Setting.scope == SettingScopeModel.GLOBAL)
            | ((Setting.scope == SettingScopeModel.USER) & (Setting.user_id == current_user.id))
            | (Setting.scope == SettingScopeModel.SITE)
        )

    rows = (await session.execute(query)).scalars().all()
    return [_to_response(r) for r in rows]


@router.put("/{key}", response_model=SettingResponse)
async def upsert_setting(
    key: str,
    payload: SettingUpsertRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SettingResponse:
    _validate_scope_access(payload.scope, current_user, payload.user_id)

    current_user_id = current_user.id
    target_user_id = payload.user_id
    if payload.scope == SettingScope.USER and target_user_id is None:
        target_user_id = current_user_id

    q = select(Setting).where(
        Setting.key == key,
        Setting.scope == SettingScopeModel(payload.scope.value),
        Setting.user_id == target_user_id,
        Setting.site_id == payload.site_id,
    )
    existing = (await session.execute(q)).scalar_one_or_none()

    if existing:
        existing.value = payload.value
        existing.updated_by = current_user_id
        await session.commit()
        await session.refresh(existing)
        return _to_response(existing)

    row = Setting(
        key=key,
        scope=SettingScopeModel(payload.scope.value),
        value=payload.value,
        user_id=target_user_id,
        site_id=payload.site_id,
        updated_by=current_user_id,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return _to_response(row)


@router.post("/bulk", response_model=list[SettingResponse])
async def bulk_upsert_settings(
    payload: SettingsBulkUpsertRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[SettingResponse]:
    out: list[SettingResponse] = []
    current_user_id = current_user.id

    for item in payload.items:
        _validate_scope_access(item.scope, current_user, item.user_id)
        target_user_id = item.user_id
        if item.scope == SettingScope.USER and target_user_id is None:
            target_user_id = current_user_id

        q = select(Setting).where(
            Setting.key == item.key,
            Setting.scope == SettingScopeModel(item.scope.value),
            Setting.user_id == target_user_id,
            Setting.site_id == item.site_id,
        )
        existing = (await session.execute(q)).scalar_one_or_none()
        if existing:
            existing.value = item.value
            existing.updated_by = current_user_id
            target = existing
        else:
            target = Setting(
                key=item.key,
                scope=SettingScopeModel(item.scope.value),
                value=item.value,
                user_id=target_user_id,
                site_id=item.site_id,
                updated_by=current_user_id,
            )
            session.add(target)

    await session.commit()

    for item in payload.items:
        target_user_id = item.user_id
        if item.scope == SettingScope.USER and target_user_id is None:
            target_user_id = current_user_id

        q = select(Setting).where(
            Setting.key == item.key,
            Setting.scope == SettingScopeModel(item.scope.value),
            Setting.user_id == target_user_id,
            Setting.site_id == item.site_id,
        )
        row = (await session.execute(q)).scalar_one()
        out.append(_to_response(row))

    return out
