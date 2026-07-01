from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class MediaFileResponse(BaseModel):
    id: str
    device_id: str
    session_id: Optional[str] = None
    original_filename: str
    stored_filename: str
    mime_type: str
    file_size: int
    sha256: str
    thumbnail_path: Optional[str] = None
    status: str
    is_complete: bool
    uploaded_time: datetime
    created_time: Optional[datetime] = None

class MediaListResponse(BaseModel):
    items: List[MediaFileResponse]
    total: int
    page: int
    page_size: int
