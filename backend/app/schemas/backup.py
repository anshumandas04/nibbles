from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class BackupStartRequest(BaseModel):
    """Initialize a backup session on the server."""
    device_id: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Unique identifier for the device (e.g., 'pixel-7-pro', 'iphone-14')",
        example="device-001"
    )
    device_name: Optional[str] = Field(
        None,
        description="Human-readable device name for dashboard display",
        example="My Phone"
    )
    platform: Optional[str] = Field(
        None, 
        pattern="^(android|ios|unknown)$",
        description="Device operating system",
        example="android"
    )
    total_files: int = Field(
        0, 
        ge=0,
        description="Expected number of files to backup",
        example=150
    )
    total_bytes: int = Field(
        0, 
        ge=0,
        description="Expected total size of files in bytes",
        example=5000000000
    )

class BackupStartResponse(BaseModel):
    """Response after starting a backup session."""
    session_id: str = Field(
        ...,
        description="Unique session identifier to use in subsequent requests",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    device_id: str = Field(
        ...,
        description="Echoed device ID",
        example="device-001"
    )
    status: str = Field(
        ...,
        description="Session status (e.g., 'active', 'completed', 'failed')",
        example="active"
    )
    started_at: datetime = Field(
        ...,
        description="UTC timestamp when session was created",
        example="2026-07-02T10:30:45.123Z"
    )

class ManifestFileEntry(BaseModel):
    """Single file entry in the manifest for deduplication checking."""
    sha256: str = Field(
        ..., 
        min_length=64, 
        max_length=64,
        description="SHA-256 hash of the file (64 hex characters)",
        example="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    size: int = Field(
        ..., 
        gt=0,
        description="File size in bytes",
        example=1500000
    )
    filename: str = Field(
        ..., 
        min_length=1,
        description="Original filename",
        example="photo_001.jpg"
    )
    mime_type: Optional[str] = Field(
        None,
        description="MIME type of the file",
        example="image/jpeg"
    )

class ManifestRequest(BaseModel):
    """Request to check which files already exist on the server (delta sync)."""
    device_id: str = Field(
        ..., 
        min_length=1, 
        max_length=255,
        description="Device identifier",
        example="device-001"
    )
    session_id: Optional[str] = Field(
        None,
        description="Session ID from backup/start endpoint",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    files: List[ManifestFileEntry] = Field(
        ...,
        description="List of files to check for existence"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "device_id": "device-001",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "files": [
                    {
                        "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                        "size": 1500000,
                        "filename": "photo_001.jpg",
                        "mime_type": "image/jpeg"
                    }
                ]
            }
        }

class ManifestResponse(BaseModel):
    """Response showing which files need to be uploaded."""
    total_received: int = Field(
        ...,
        description="Total number of files received in manifest",
        example=100
    )
    already_exists: int = Field(
        ...,
        description="Number of files already stored on server",
        example=75
    )
    missing: List[str] = Field(
        ...,
        description="List of SHA-256 hashes of files not yet on server",
        example=["4a28f8df4d877e68...", "f626c8cb2890250b..."]
    )
    bytes_saved: int = Field(
        ...,
        description="Data saved by deduplication (in bytes)",
        example=4500000000
    )

class SessionResponse(BaseModel):
    """Complete backup session information."""
    id: str = Field(
        ...,
        description="Session unique identifier",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    device_id: str = Field(
        ...,
        description="Associated device ID",
        example="device-001"
    )
    started_at: datetime = Field(
        ...,
        description="When session was started",
        example="2026-07-02T10:30:45.123Z"
    )
    completed_at: Optional[datetime] = Field(
        None,
        description="When session was completed (if completed)",
        example="2026-07-02T11:45:30.456Z"
    )
    status: str = Field(
        ...,
        description="Current session status",
        example="active"
    )
    total_files: int = Field(
        ...,
        description="Total files expected to upload",
        example=150
    )
    uploaded_files: int = Field(
        ...,
        description="Number of files successfully uploaded",
        example=75
    )
    total_bytes: int = Field(
        ...,
        description="Total expected bytes",
        example=5000000000
    )
    uploaded_bytes: int = Field(
        ...,
        description="Bytes uploaded so far",
        example=2500000000
    )
    progress_percent: float = Field(
        ...,
        description="Completion percentage (0-100)",
        example=50.0
    )
