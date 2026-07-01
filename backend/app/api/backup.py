from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.core.security import verify_api_key
from app.services.backup_service import BackupService
from app.schemas.backup import (
    BackupStartRequest, BackupStartResponse,
    ManifestRequest, ManifestResponse, SessionResponse
)
from app.schemas.common import SuccessResponse

router = APIRouter(
    prefix="/backup",
    tags=["Backup"],
    dependencies=[Depends(verify_api_key)]
)


@router.post(
    "/start",
    response_model=BackupStartResponse,
    summary="Start a Backup Session",
    description="Initialize a new backup session for a device. Returns a session_id needed for manifest and upload endpoints."
)
async def start_backup(
    request: BackupStartRequest,
    db: AsyncSession = Depends(get_db)
):
    """Start a new backup session.
    
    **Flow:**
    1. Device provides device_id and metadata
    2. Server creates session record
    3. Returns session_id for subsequent requests
    
    **Next:** Use session_id in /backup/manifest endpoint
    """
    service = BackupService(db)
    return await service.start_session(request)


@router.post(
    "/manifest",
    response_model=ManifestResponse,
    summary="Check File Manifest (Delta Sync)",
    description="Submit file hashes to identify missing files. Server responds with list of files that need uploading, enabling deduplication and bandwidth optimization."
)
async def check_manifest(
    request: ManifestRequest,
    db: AsyncSession = Depends(get_db)
):
    """Check which files are missing on the server.
    
    **Key Benefits:**
    - **Deduplication:** Identifies files already stored
    - **Bandwidth Saving:** Only missing files need uploading
    - **Smart Sync:** Avoids re-uploading duplicate content
    
    **Next:** Upload only files in 'missing' list to /upload
    """
    service = BackupService(db)
    return await service.check_manifest(request)


@router.get(
    "/session/{session_id}",
    response_model=SessionResponse,
    summary="Get Session Details",
    description="Retrieve complete session information including progress metrics and timestamps."
)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get complete session information.
    
    **Returns:**
    - Session status and timestamps
    - Progress metrics (% complete)
    - File/byte counters
    """
    service = BackupService(db)
    return await service.get_session(session_id)


@router.delete(
    "/session/{session_id}",
    response_model=SuccessResponse,
    summary="Delete Backup Session",
    description="Remove session record. Note: Only metadata is deleted; uploaded files remain on server."
)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete a backup session.
    
    **Warning:** This deletes metadata only. Uploaded files remain.
    """
    service = BackupService(db)
    deleted = await service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return SuccessResponse(message="Backup session deleted successfully")"
