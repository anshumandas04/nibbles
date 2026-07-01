from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from app.schemas.backup import SessionResponse

class UploadResponse(BaseModel):
    success: bool = True
    upload_id: str
    stored_filename: str
    sha256: str
    size: int
    is_duplicate: bool = False
    created_at: datetime

class UploadCompleteRequest(BaseModel):
    upload_id: str
    sha256: str = Field(..., min_length=64, max_length=64)

class UploadCompleteResponse(BaseModel):
    success: bool = True
    upload_id: str
    verified: bool
    message: str

class UploadFailureRequest(BaseModel):
    device_id: str
    original_filename: str
    sha256: Optional[str] = None
    error_message: str

class UploadSummary(BaseModel):
    id: str
    original_filename: str
    size: int
    status: str
    uploaded_time: datetime

class UploadStatusResponse(BaseModel):
    device_id: str
    active_session: Optional[SessionResponse] = None
    recent_uploads: List[UploadSummary]
    failed_count: int
