"""Site endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.db.postgres import get_session
from app.models.models import Site
from app.schemas.schemas import SiteCreate, SiteResponse, SiteUpdate

router = APIRouter(prefix="/sites", tags=["sites"])


@router.get("", response_model=list[SiteResponse], dependencies=[Depends(require_permission(Permission.ASSET_READ))])
async def list_sites(session: AsyncSession = Depends(get_session)) -> list[SiteResponse]:
    """List industrial sites."""
    result = await session.execute(select(Site).where(Site.is_active.is_(True)))
    sites = list(result.scalars().all())
    return [
        SiteResponse(
            id=site.id,
            name=site.name,
            description=site.description,
            location=site.location,
            sector=site.sector,
            timezone=site.timezone,
            metadata=site.metadata_json or {},
            is_active=site.is_active,
            created_at=site.created_at,
            updated_at=site.updated_at,
        )
        for site in sites
    ]


@router.get("/{site_id}", response_model=SiteResponse, dependencies=[Depends(require_permission(Permission.ASSET_READ))])
async def get_site(site_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> SiteResponse:
    """Get site by id."""
    result = await session.execute(select(Site).where(Site.id == site_id, Site.is_active.is_(True)))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")
    return SiteResponse(
        id=site.id,
        name=site.name,
        description=site.description,
        location=site.location,
        sector=site.sector,
        timezone=site.timezone,
        metadata=site.metadata_json or {},
        is_active=site.is_active,
        created_at=site.created_at,
        updated_at=site.updated_at,
    )


@router.post("", response_model=SiteResponse, dependencies=[Depends(require_permission(Permission.ASSET_CREATE))])
async def create_site(payload: SiteCreate, session: AsyncSession = Depends(get_session)) -> SiteResponse:
    """Create industrial site."""
    site = Site(
        name=payload.name,
        description=payload.description,
        location=payload.location,
        sector=payload.sector.value,
        timezone=payload.timezone,
        metadata_json=payload.metadata,
        is_active=True,
    )
    session.add(site)
    await session.commit()
    await session.refresh(site)
    return SiteResponse(
        id=site.id,
        name=site.name,
        description=site.description,
        location=site.location,
        sector=site.sector,
        timezone=site.timezone,
        metadata=site.metadata_json or {},
        is_active=site.is_active,
        created_at=site.created_at,
        updated_at=site.updated_at,
    )


@router.patch("/{site_id}", response_model=SiteResponse, dependencies=[Depends(require_permission(Permission.ASSET_CREATE))])
async def update_site(site_id: uuid.UUID, payload: SiteUpdate, session: AsyncSession = Depends(get_session)) -> SiteResponse:
    """Update industrial site information."""
    result = await session.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    update_data = payload.model_dump(exclude_unset=True)

    if "name" in update_data:
        site.name = update_data["name"]
    if "description" in update_data:
        site.description = update_data["description"]
    if "location" in update_data:
        site.location = update_data["location"]
    if "sector" in update_data and update_data["sector"] is not None:
        site.sector = update_data["sector"].value
    if "timezone" in update_data:
        site.timezone = update_data["timezone"]
    if "metadata" in update_data and update_data["metadata"] is not None:
        site.metadata_json = update_data["metadata"]
    if "is_active" in update_data and update_data["is_active"] is not None:
        site.is_active = update_data["is_active"]

    await session.commit()
    await session.refresh(site)

    return SiteResponse(
        id=site.id,
        name=site.name,
        description=site.description,
        location=site.location,
        sector=site.sector,
        timezone=site.timezone,
        metadata=site.metadata_json or {},
        is_active=site.is_active,
        created_at=site.created_at,
        updated_at=site.updated_at,
    )


@router.post("/{site_id}/activate", response_model=SiteResponse, dependencies=[Depends(require_permission(Permission.ASSET_CREATE))])
async def activate_site(site_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> SiteResponse:
    """Activate site."""
    result = await session.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    site.is_active = True
    await session.commit()
    await session.refresh(site)

    return SiteResponse(
        id=site.id,
        name=site.name,
        description=site.description,
        location=site.location,
        sector=site.sector,
        timezone=site.timezone,
        metadata=site.metadata_json or {},
        is_active=site.is_active,
        created_at=site.created_at,
        updated_at=site.updated_at,
    )


@router.post("/{site_id}/deactivate", response_model=SiteResponse, dependencies=[Depends(require_permission(Permission.ASSET_CREATE))])
async def deactivate_site(site_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> SiteResponse:
    """Deactivate site."""
    result = await session.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    site.is_active = False
    await session.commit()
    await session.refresh(site)

    return SiteResponse(
        id=site.id,
        name=site.name,
        description=site.description,
        location=site.location,
        sector=site.sector,
        timezone=site.timezone,
        metadata=site.metadata_json or {},
        is_active=site.is_active,
        created_at=site.created_at,
        updated_at=site.updated_at,
    )


@router.delete("/{site_id}", status_code=status.HTTP_200_OK, response_model=dict, dependencies=[Depends(require_permission(Permission.ASSET_CREATE))])
async def delete_site(site_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> dict:
    """Soft delete site."""
    result = await session.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    site.is_active = False
    await session.commit()
    return {"status": "ok"}
