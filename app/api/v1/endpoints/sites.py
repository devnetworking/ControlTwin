"""Site endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.db.postgres import get_session
from app.models.models import Site
from app.schemas.schemas import SiteCreate, SiteResponse

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=list[SiteResponse], dependencies=[Depends(require_permission(Permission.ASSET_READ))])
async def list_sites(session: AsyncSession = Depends(get_session)) -> list[Site]:
    """List industrial sites."""
    result = await session.execute(select(Site).where(Site.is_active.is_(True)))
    return list(result.scalars().all())


@router.get("/{site_id}", response_model=SiteResponse, dependencies=[Depends(require_permission(Permission.ASSET_READ))])
async def get_site(site_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Site:
    """Get site by id."""
    result = await session.execute(select(Site).where(Site.id == site_id, Site.is_active.is_(True)))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return site


@router.post("", response_model=SiteResponse, dependencies=[Depends(require_permission(Permission.ASSET_CREATE))])
async def create_site(payload: SiteCreate, session: AsyncSession = Depends(get_session)) -> Site:
    """Create industrial site."""
    site = Site(
        name=payload.name,
        description=payload.description,
        location=payload.location,
        sector=payload.sector,
        timezone=payload.timezone,
        metadata_json=payload.metadata,
        is_active=True,
    )
    session.add(site)
    await session.commit()
    await session.refresh(site)
    return site
