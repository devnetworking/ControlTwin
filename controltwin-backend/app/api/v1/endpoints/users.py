"""User endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.rbac import Permission, require_permission
from app.db.postgres import get_session
from app.models.models import User
from app.schemas.schemas import UserCreate, UserResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> User:
    """Return current authenticated user."""
    return current_user


@router.post("", response_model=UserResponse, dependencies=[Depends(require_permission(Permission.USER_MANAGE))])
async def create_user(payload: UserCreate, session: AsyncSession = Depends(get_session)) -> User:
    """Create user (requires user:manage)."""
    service = UserService(session)
    return await service.create_user(payload)
