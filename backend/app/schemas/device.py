from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class DeviceSyncResponse(BaseModel):
    """Synchronization status for a device."""
    device_id: str = Field(
        ...,
        description="Device unique identifier",
        example="device-001"
    )
    last_backup: Optional[datetime] = Field(
        None,
        description="Timestamp of last successful backup",
        example="2026-07-02T10:35:20.789Z"
    )
    uploaded_count: int = Field(
        0,
        description="Total number of files uploaded from this device",
        example=150
    )
    total_size_bytes: int = Field(
        0,
        description="Total data uploaded from this device in bytes",
        example=5000000000
    )
    remaining: int = Field(
        0,
        description="Estimated remaining files to backup",
        example=50
    )
    last_seen: Optional[datetime] = Field(
        None,
        description="Last time device connected to server",
        example="2026-07-02T11:00:00.000Z"
    )

class DeviceInfo(BaseModel):
    """Basic device information."""
    device_id: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Unique identifier for the device",
        example="device-001"
    )
    name: Optional[str] = Field(
        None,
        description="Human-readable device name",
        example="My Phone"
    )
    platform: Optional[str] = Field(
        None, 
        pattern="^(android|ios|unknown)$",
        description="Device operating system",
        example="android"
    )
