from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class MediaFileResponse(BaseModel):
    """Complete information about a stored media file."""
    id: str = Field(
        ...,
        description="Media file unique identifier",
        example="550e8400-e29b-41d4-a716-446655440000"
    )
    device_id: str = Field(
        ...,
        description="Device that uploaded this file",
        example="device-001"
    )
    session_id: Optional[str] = Field(
        None,
        description="Backup session ID during which file was uploaded",
        example="550e8400-e29b-41d4-a716-446655440001"
    )
    original_filename: str = Field(
        ...,
        description="Original filename from device",
        example="photo_001.jpg"
    )
    stored_filename: str = Field(
        ...,
        description="Filename as stored on server (UUID-based)",
        example="cb03164ad0e74f828a2a89feeb61d0bf.jpg"
    )
    mime_type: str = Field(
        ...,
        description="MIME type of the file",
        example="image/jpeg"
    )
    file_size: int = Field(
        ...,
        description="File size in bytes",
        example=2000000
    )
    sha256: str = Field(
        ...,
        description="SHA-256 hash of the file",
        example="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    thumbnail_path: Optional[str] = Field(
        None,
        description="Path to thumbnail if available",
        example="thumbnails/thumb_cb03164ad0e74f828a2a89feeb61d0bf.jpg"
    )
    status: str = Field(
        ...,
        description="File status (e.g., 'completed', 'pending', 'failed')",
        example="completed"
    )
    is_complete: bool = Field(
        ...,
        description="Whether upload is fully complete and verified",
        example=True
    )
    uploaded_time: datetime = Field(
        ...,
        description="When file was uploaded",
        example="2026-07-02T10:35:20.789Z"
    )
    created_time: Optional[datetime] = Field(
        None,
        description="Original file creation time from device",
        example="2026-07-01T15:30:00.000Z"
    )

class MediaListResponse(BaseModel):
    """Paginated list of media files."""
    items: List[MediaFileResponse] = Field(
        ...,
        description="List of media file records"
    )
    total: int = Field(
        ...,
        description="Total number of media files in database",
        example=500
    )
    page: int = Field(
        ...,
        description="Current page number (1-indexed)",
        example=1
    )
    page_size: int = Field(
        ...,
        description="Number of items per page",
        example=20
    )
