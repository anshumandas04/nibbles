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
        description="Unique identifier for this upload",
        example="3be5cf22-901d-4008-8e6d-2dcf1e73998b"
    )
    stored_filename: str = Field(
        ...,
        description="Filename as stored on server (UUID-based for security)",
        example="cb03164ad0e74f828a2a89feeb61d0bf.jpg"
    )
    sha256: str = Field(
        ...,
        description="SHA-256 hash of uploaded file",
        example="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
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

class UploadCompleteRequest(BaseModel):
    """Request to verify upload integrity."""
    upload_id: str = Field(
        ...,
        description="Upload ID from the upload response",
        example="3be5cf22-901d-4008-8e6d-2dcf1e73998b"
    )
    sha256: str = Field(
        ..., 
        min_length=64, 
        max_length=64,
        description="SHA-256 hash to verify against stored file",
        example="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )

class UploadCompleteResponse(BaseModel):
    """Response after upload integrity verification."""
    success: bool = Field(
        True,
        description="Whether verification succeeded"
    )
    upload_id: str = Field(
        ...,
        description="Upload ID that was verified",
        example="3be5cf22-901d-4008-8e6d-2dcf1e73998b"
    )
    verified: bool = Field(
        ...,
        description="Whether SHA-256 verification passed",
        example=True
    )
    message: str = Field(
        ...,
        description="Human-readable verification result",
        example="Verification successful"
    )

class UploadFailureRequest(BaseModel):
    """Report a failed upload to the server."""
    device_id: str = Field(
        ...,
        description="Device that attempted upload",
        example="device-001"
    )
    original_filename: str = Field(
        ...,
        description="Name of the file that failed to upload",
        example="photo.jpg"
    )
    sha256: Optional[str] = Field(
        None,
        description="SHA-256 of the file (if available)",
        example="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    )
    error_message: str = Field(
        ...,
        description="Error message explaining the failure",
        example="Network timeout during upload"
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
