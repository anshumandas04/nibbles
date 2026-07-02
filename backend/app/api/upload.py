from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from uuid import UUID
from app.database.database import get_db
from app.core.security import verify_api_key
from app.services.upload_service import UploadService
from app.services.storage_service import StorageService, get_storage_service
from app.schemas.upload import UploadResponse, UploadStatusResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/upload",
    tags=["Upload"],
    dependencies=[Depends(verify_api_key)]
)


@router.post(
    "",
    response_model=UploadResponse,
    summary="Upload a File",
    description="Upload a file for backup. Server computes SHA256, detects MIME type, and generates UUID. Single request completes the upload."
)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    device_id: str = Form(...),
    session_id: str | None = Form(None),
    created_time: datetime | None = Form(None),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    """Upload a file for backup.
    
    The server handles:
    - SHA256 computation during streaming
    - MIME type detection
    - UUID generation
    - Deduplication check
    
    Minimal client requirements:
    - File (required)
    - device_id (required)
    - session_id (optional)
    - created_time (optional)
    """
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Use filename from file or fallback to a default
    original_filename = file.filename or "unnamed_file"
    
    # Stream file and compute metadata in one pass
    file_metadata = await storage.save_file_with_hash(file, original_filename)
    
    # Check for duplicates
    service = UploadService(db, storage)
    duplicate = await service.check_duplicate(file_metadata['sha256'])
    
    if duplicate:
        # File already exists - return existing file info
        return UploadResponse(
            success=True,
            upload_id=duplicate.id,
            stored_filename=duplicate.relative_path.split("/")[-1],
            sha256=duplicate.sha256,
            size=duplicate.size,
            is_duplicate=True,
            created_at=duplicate.created_at,
            mime_type=duplicate.mime_type
        )
    
    # Save new file metadata to database
    media_file = await service.save_file_metadata(
        upload_id=file_metadata['upload_id'],
        device_id=device_id,
        session_id=session_id,
        original_filename=file_metadata['original_filename'],
        stored_filename=file_metadata['stored_filename'],
        sha256=file_metadata['sha256'],
        mime_type=file_metadata['mime_type'],
        size=file_metadata['size'],
        relative_path=file_metadata['relative_path'],
        created_time=created_time,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    return UploadResponse(
        success=True,
        upload_id=file_metadata['upload_id'],
        stored_filename=file_metadata['stored_filename'],
        sha256=file_metadata['sha256'],
        size=file_metadata['size'],
        is_duplicate=False,
        created_at=media_file.created_at,
        mime_type=file_metadata['mime_type']
    )


@router.get(
    "/status/{device_id}",
    response_model=UploadStatusResponse,
    summary="Get Upload Status",
    description="Get upload status for a device"
)
async def get_upload_status(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    service = UploadService(db, storage)
    return await service.get_upload_status(device_id)

