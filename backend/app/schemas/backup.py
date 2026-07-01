from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class BackupStartRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=255)
    device_name: Optional[str] = None
    platform: Optional[str] = Field(None, pattern="^(android|ios|unknown)$")
    total_files: int = Field(0, ge=0)
    total_bytes: int = Field(0, ge=0)

class BackupStartResponse(BaseModel):
    session_id: str
    device_id: str
    status: str
    started_at: datetime

class ManifestFileEntry(BaseModel):
    sha256: str = Field(..., min_length=64, max_length=64)
    size: int = Field(..., gt=0)
    filename: str = Field(..., min_length=1)
    mime_type: Optional[str] = None

class ManifestRequest(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=255)
    session_id: Optional[str] = None
    files: List[ManifestFileEntry]

class ManifestResponse(BaseModel):
    total_received: int
    already_exists: int
    missing: List[str]  # List of missing SHA-256 hashes
    bytes_saved: int  # Deduplication storage savings in bytes

class SessionResponse(BaseModel):
    id: str
    device_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    total_files: int
    uploaded_files: int
    total_bytes: int
    uploaded_bytes: int
    progress_percent: float
