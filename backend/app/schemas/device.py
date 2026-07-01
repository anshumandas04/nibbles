from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class DeviceSyncResponse(BaseModel):
    device_id: str
    last_backup: Optional[datetime] = None
    uploaded_count: int = 0
    total_size_bytes: int = 0
    remaining: int = 0
    last_seen: Optional[datetime] = None

class DeviceInfo(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=255)
    name: Optional[str] = None
    platform: Optional[str] = Field(None, pattern="^(android|ios|unknown)$")
