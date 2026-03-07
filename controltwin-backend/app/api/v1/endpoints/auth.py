"""Authentication endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_session
from app.schemas.schemas import LoginRequest, RefreshRequest, TokenResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    """Authenticate user and return access/refresh tokens."""
    service = UserService(session)
    return await service.authenticate(payload.username, payload.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, session: AsyncSession = Depends(get_session)) -> TokenResponse:
    """Refresh access/refresh token pair."""
    service = UserService(session)
    return await service.refresh_tokens(payload.refresh_token)
