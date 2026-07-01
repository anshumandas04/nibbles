"""Device repository for database CRUD operations on Device model.

Handles device registration, lookup, and last-seen timestamp updates.
"""

import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Device


class DeviceRepository:
    """Repository class encapsulating all database operations for the Device model."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository with an async database session.

        Args:
            db: SQLAlchemy async session instance.
        """
        self.db = db

    async def get_by_device_id(self, device_id: str) -> Device | None:
        """Retrieve a device by its unique client-assigned device identifier.

        Args:
            device_id: The unique client-side device identifier string.

        Returns:
            The Device instance if found, otherwise None.
        """
        result = await self.db.execute(
            select(Device).where(Device.device_id == device_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        device_id: str,
        name: str | None = None,
        platform: str | None = None,
    ) -> Device:
        """Retrieve an existing device or create a new one.

        If the device already exists, updates its last_seen timestamp and
        optionally updates name and platform if provided. If the device
        does not exist, creates a new record.

        Args:
            device_id: The unique client-side device identifier.
            name: Optional human-readable device name.
            platform: Optional platform string (e.g., 'android', 'ios').

        Returns:
            The existing or newly created Device instance.
        """
        device = await self.get_by_device_id(device_id)
        if device:
            device.last_seen = datetime.datetime.now(datetime.timezone.utc)
            if name:
                device.name = name
            if platform:
                device.platform = platform
            return device

        device = Device(
            device_id=device_id,
            name=name,
            platform=platform,
        )
        self.db.add(device)
        await self.db.flush()
        return device

    async def update_last_seen(self, device_id: str) -> None:
        """Update the last_seen timestamp for a device.

        Args:
            device_id: The unique client-side device identifier.
        """
        device = await self.get_by_device_id(device_id)
        if device:
            device.last_seen = datetime.datetime.now(datetime.timezone.utc)
