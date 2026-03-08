"""User endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.rbac import Permission, require_permission
from app.db.postgres import get_session
from app.models.models import User
from app.schemas.schemas import UserCreate, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Return current authenticated user."""
    return current_user


@router.get("", response_model=list[UserResponse], dependencies=[Depends(require_permission(Permission.USER_MANAGE))])
async def list_users(session: AsyncSession = Depends(get_session)) -> list[User]:
    """List users (requires user:manage)."""
    service = UserService(session)
    return await service.list_users()


@router.post("", response_model=UserResponse, dependencies=[Depends(require_permission(Permission.USER_MANAGE))])
async def create_user(payload: UserCreate, session: AsyncSession = Depends(get_session)) -> User:
    """Create user (requires user:manage)."""
    service = UserService(session)
    return await service.create_user(payload)


@router.patch("/{user_id}", response_model=UserResponse, dependencies=[Depends(require_permission(Permission.USER_MANAGE))])
async def update_user(user_id: uuid.UUID, payload: UserUpdate, session: AsyncSession = Depends(get_session)) -> User:
    """Update user (requires user:manage)."""
    service = UserService(session)
    return await service.update_user(str(user_id), payload)


@router.post("/{user_id}/activate", response_model=UserResponse, dependencies=[Depends(require_permission(Permission.USER_MANAGE))])
async def activate_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> User:
    """Activate user (requires user:manage)."""
    service = UserService(session)
    return await service.activate_user(str(user_id))


@router.post("/{user_id}/deactivate", response_model=UserResponse, dependencies=[Depends(require_permission(Permission.USER_MANAGE))])
async def deactivate_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> User:
    """Deactivate user (requires user:manage)."""
    service = UserService(session)
    return await service.deactivate_user(str(user_id))


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_permission(Permission.USER_MANAGE))])
async def delete_user(user_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Response:
    """Delete user (requires user:manage)."""
    service = UserService(session)
    await service.delete_user(str(user_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
