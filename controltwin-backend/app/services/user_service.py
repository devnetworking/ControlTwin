"""User service for authentication and account lifecycle."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.models.models import User
from app.schemas.schemas import TokenResponse, UserCreate, UserUpdate


class UserService:
    """Service handling users and auth flows."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def authenticate(self, username: str, password: str) -> TokenResponse:
        """Authenticate user with lockout policy."""
        result = await self.session.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        now = datetime.now(timezone.utc)
        if user.locked_until and user.locked_until > now:
            raise HTTPException(status_code=status.HTTP_423_LOCKED, detail="Account is temporarily locked")

        if not verify_password(password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= settings.MAX_FAILED_LOGIN_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=settings.ACCOUNT_LOCK_MINUTES)
            await self.session.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = now

        # Capture values before commit to avoid async lazy-load after expiration.
        user_id = str(user.id)
        username_value = user.username
        role_value = user.role.value
        role_enum = user.role

        access = create_access_token(user_id, username_value, role_value)
        refresh = create_refresh_token(user_id, username_value, role_value)

        await self.session.commit()

        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            role=role_enum,
        )

    async def create_user(self, payload: UserCreate) -> User:
        """Create user account."""
        existing_username = await self.session.execute(select(User).where(User.username == payload.username))
        if existing_username.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")

        existing_email = await self.session.execute(select(User).where(User.email == payload.email))
        if existing_email.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

        user = User(
            username=payload.username,
            email=str(payload.email),
            hashed_password=hash_password(payload.password),
            role=payload.role,
            is_active=True,
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def list_users(self) -> list[User]:
        """List all users."""
        result = await self.session.execute(select(User).order_by(User.created_at.desc()))
        return list(result.scalars().all())

    async def update_user(self, user_id: str, payload: UserUpdate) -> User:
        """Update user fields."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        updates = payload.model_dump(exclude_unset=True)
        if "email" in updates and updates["email"] != user.email:
            existing_email = await self.session.execute(select(User).where(User.email == updates["email"]))
            existing = existing_email.scalar_one_or_none()
            if existing and existing.id != user.id:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")

        for key, value in updates.items():
            setattr(user, key, value)

        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def activate_user(self, user_id: str) -> User:
        """Activate user account."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.is_active = True
        user.locked_until = None
        user.failed_login_attempts = 0
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def deactivate_user(self, user_id: str) -> User:
        """Deactivate user account."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        user.is_active = False
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def delete_user(self, user_id: str) -> None:
        """Delete user account."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        await self.session.delete(user)
        await self.session.commit()

    async def refresh_tokens(self, refresh_token: str) -> TokenResponse:
        """Refresh access and refresh tokens."""
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = payload.get("sub")
        username = payload.get("username")
        role = payload.get("role")
        if not user_id or not username or not role:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")

        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

        new_access = create_access_token(str(user.id), user.username, user.role.value)
        new_refresh = create_refresh_token(str(user.id), user.username, user.role.value)
        return TokenResponse(
            access_token=new_access,
            refresh_token=new_refresh,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            role=user.role,
        )
