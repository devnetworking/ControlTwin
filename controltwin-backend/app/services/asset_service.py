"""Asset service for CRUD operations with soft-delete semantics."""

from __future__ import annotations

import socket
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from pymodbus.client import ModbusTcpClient

from app.models.models import Asset, AssetStatus
from app.schemas.schemas import AssetCreate, AssetUpdate


class AssetService:
    """Service for asset operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _detect_connectivity_status(
        protocol: str | None, ip_address: str | None, port: int | None
    ) -> tuple[str, datetime | None]:
        """Detect connectivity status with protocol-aware checks."""
        if not ip_address or not port:
            return "unknown", None

        protocol_value = (protocol or "").lower()

        # Protocol-aware check for Modbus TCP: only online when a real Modbus request succeeds.
        if protocol_value == "modbus_tcp":
            client = ModbusTcpClient(host=ip_address, port=port, timeout=1.5)
            try:
                if not client.connect():
                    return "offline", None
                rr = client.read_holding_registers(address=0, count=1, slave=1)
                if rr.isError():
                    return "offline", None
                return "online", datetime.now(timezone.utc)
            except Exception:
                return "offline", None
            finally:
                try:
                    client.close()
                except Exception:
                    pass

        # Fallback for other protocols: basic TCP reachability.
        try:
            with socket.create_connection((ip_address, port), timeout=1.5):
                return "online", datetime.now(timezone.utc)
        except OSError:
            return "offline", None

    async def _refresh_asset_runtime_status(self, asset: Asset) -> None:
        """Refresh asset runtime status from live protocol check and update model in memory."""
        detected_status, detected_last_seen = self._detect_connectivity_status(
            str(asset.protocol), asset.ip_address, asset.port
        )

        new_status = AssetStatus(detected_status)
        if asset.status != new_status:
            asset.status = new_status
        asset.last_seen = detected_last_seen

    async def list_assets(
        self,
        site_id: uuid.UUID | None = None,
        asset_type: str | None = None,
        status_value: str | None = None,
        criticality: str | None = None,
        protocol: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> list[Asset]:
        """List assets with filters and pagination."""
        filters = [Asset.is_active.is_(True)]
        if site_id:
            filters.append(Asset.site_id == site_id)
        if asset_type:
            filters.append(Asset.asset_type == asset_type)
        if status_value:
            filters.append(Asset.status == status_value)
        if criticality:
            filters.append(Asset.criticality == criticality)
        if protocol:
            filters.append(Asset.protocol == protocol)

        stmt = select(Asset).where(and_(*filters)).offset((page - 1) * size).limit(size)
        result = await self.session.execute(stmt)
        assets = list(result.scalars().all())

        for asset in assets:
            await self._refresh_asset_runtime_status(asset)

        # Flush updates without expiring loaded instances to avoid lazy reload in response mapping.
        if assets:
            await self.session.flush()

        return assets

    async def get_or_404(self, asset_id: uuid.UUID) -> Asset:
        """Get asset or raise 404."""
        result = await self.session.execute(select(Asset).where(Asset.id == asset_id, Asset.is_active.is_(True)))
        asset = result.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")

        await self._refresh_asset_runtime_status(asset)
        # Flush updates while keeping loaded state intact for response serialization.
        await self.session.flush()
        return asset

    async def create_asset(self, payload: AssetCreate) -> Asset:
        """Create asset with unique site+tag validation."""
        duplicate = await self.session.execute(
            select(Asset).where(
                Asset.site_id == payload.site_id,
                Asset.tag == payload.tag,
                Asset.is_active.is_(True),
            )
        )
        if duplicate.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset tag already exists in site")

        detected_status, detected_last_seen = self._detect_connectivity_status(
            str(payload.protocol), payload.ip_address, payload.port
        )

        # Ensure enum-typed columns always receive enum members (not raw strings)
        # to avoid DB/ORM adaptation issues that can surface as HTTP 500 on create.
        asset_status = AssetStatus(detected_status)

        asset = Asset(
            site_id=payload.site_id,
            parent_id=payload.parent_id,
            name=payload.name,
            tag=payload.tag,
            description=payload.description,
            asset_type=payload.asset_type,
            protocol=payload.protocol,
            ip_address=payload.ip_address,
            port=payload.port,
            vendor=payload.vendor,
            model=payload.model,
            firmware_version=payload.firmware_version,
            purdue_level=payload.purdue_level,
            criticality=payload.criticality,
            status=asset_status,
            metadata_json=payload.metadata,
            is_active=True,
            last_seen=detected_last_seen,
        )
        self.session.add(asset)
        await self.session.commit()
        await self.session.refresh(asset)
        return asset

    async def update_asset(self, asset_id: uuid.UUID, payload: AssetUpdate) -> Asset:
        """Update mutable fields of an asset."""
        asset = await self.get_or_404(asset_id)
        data = payload.model_dump(exclude_unset=True)
        if "metadata" in data:
            data["metadata_json"] = data.pop("metadata")
        for key, value in data.items():
            setattr(asset, key, value)
        asset.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(asset)
        return asset

    async def delete_asset(self, asset_id: uuid.UUID) -> None:
        """Soft delete asset only."""
        asset = await self.get_or_404(asset_id)
        asset.is_active = False
        asset.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
