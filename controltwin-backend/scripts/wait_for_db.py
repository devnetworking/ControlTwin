#!/usr/bin/env python3
"""Wait for PostgreSQL to be ready."""
import asyncio
import os
import re
import sys
from urllib.parse import quote_plus

import asyncpg


def _normalize_database_url(raw_url: str) -> str:
    if not raw_url:
        return raw_url
    return re.sub(r"^postgresql\+asyncpg://", "postgresql://", raw_url)


def _build_database_url_from_postgres_env() -> str:
    user = os.getenv("POSTGRES_USER", "controltwin")
    password = os.getenv("POSTGRES_PASSWORD", "controltwin")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "controltwin")

    user_enc = quote_plus(user)
    password_enc = quote_plus(password)
    return f"postgresql://{user_enc}:{password_enc}@{host}:{port}/{db}"


def _resolve_database_url() -> tuple[str, str]:
    raw_url = os.getenv("DATABASE_URL", "").strip()
    if raw_url:
        normalized = _normalize_database_url(raw_url)
        return normalized, "DATABASE_URL"

    fallback = _build_database_url_from_postgres_env()
    return fallback, "POSTGRES_* fallback"


async def wait_for_db(max_retries=30, delay=2):
    url, source = _resolve_database_url()
    if not url.startswith("postgresql://"):
        print(f"ERROR: Resolved database URL from {source} is invalid.")
        print("Expected scheme: postgresql://")
        sys.exit(1)

    print(f"Using database URL source: {source}")

    for attempt in range(max_retries):
        try:
            conn = await asyncpg.connect(url)
            await conn.execute("SELECT 1")
            await conn.close()
            print(f"PostgreSQL ready after {attempt + 1} attempt(s)")
            return True
        except Exception as e:
            print(f"Attempt {attempt + 1}/{max_retries}: DB not ready ({e})")
            await asyncio.sleep(delay)

    print("ERROR: PostgreSQL not available after max retries")
    sys.exit(1)


if __name__ == "__main__":
    asyncio.run(wait_for_db())
