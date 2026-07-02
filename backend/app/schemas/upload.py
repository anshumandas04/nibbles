from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.schemas.backup import SessionResponse

class UploadResponse(BaseModel):
    """Response after successfully uploading a file."""
    success: bool = Field(
        True,
        description="Whether upload was successful"
    )
    upload_id: str = Field(
        ...,
        description="Unique identifier for this upload (UUID)",
        example="3be5cf22-901d-4008-8e6d-2dcf1e73998b"
    )
    stored_filename: str = Field(
        ...,
        description="Filename as stored on server (UUID-based for security)",
        example="3be5cf22-901d-4008-8e6d-2dcf1e73998b.jpg"
    )
    sha256: str = Field(
        ...,
        description="SHA-256 hash computed by server during upload",
        example="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    mime_type: str = Field(
        ...,
        description="MIME type detected by server (using python-magic)",
        example="image/jpeg"
    )
    size: int = Field(
        ...,
        description="File size in bytes",
        example=2000000
    )
    is_duplicate: bool = Field(
        False,
        description="True if this file was already stored (deduplication)",
        example=False
    )
    created_at: datetime = Field(
        ...,
        description="Upload completion timestamp",
        example="2026-07-02T10:35:20.789Z"
    )


class UploadSummary(BaseModel):
    """Summary of a recent upload."""
    id: str = Field(
        ...,
        description="Upload ID",
        example="3be5cf22-901d-4008-8e6d-2dcf1e73998b"
    )
    original_filename: str = Field(
        ...,
        description="Original filename",
        example="photo.jpg"
    )
    size: int = Field(
        ...,
        description="File size in bytes",
        example=2000000
    )
    status: str = Field(
        ...,
        description="Upload status (e.g., 'completed', 'pending', 'failed')",
        example="completed"
    )
    uploaded_time: datetime = Field(
        ...,
        description="When file was uploaded",
        example="2026-07-02T10:35:20.789Z"
    )

class UploadStatusResponse(BaseModel):
    """Overall upload status for a device."""
    device_id: str = Field(
        ...,
        description="Device identifier",
        example="device-001"
    )
    active_session: Optional[SessionResponse] = Field(
        None,
        description="Currently active backup session (if any)"
    )
    recent_uploads: List[UploadSummary] = Field(
        ...,
        description="List of recently uploaded files"
    )
    failed_count: int = Field(
        ...,
        description="Number of failed uploads",
        example=0
    )
