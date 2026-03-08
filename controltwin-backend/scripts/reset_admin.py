from __future__ import annotations

import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.db.postgres import SessionLocal
from app.models.models import User

USERNAME = "admin"
NEW_PASSWORD = "ControlTwin2025!"


async def main() -> None:
    async with SessionLocal() as session:
        result = await session.execute(select(User).where(User.username == USERNAME))
        user = result.scalar_one_or_none()
        if not user:
            print("admin user not found")
            return

        user.hashed_password = hash_password(NEW_PASSWORD)
        user.failed_login_attempts = 0
        user.locked_until = None
        user.is_active = True

        await session.commit()
        print("admin credentials reset and account unlocked")


if __name__ == "__main__":
    asyncio.run(main())
