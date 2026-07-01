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
    description="Initialize a new backup session for a device. Returns a session_id needed for manifest and upload endpoints.",
    tags=["Backup"],
    responses={
        200: {"description": "Backup session created successfully"},
        401: {"description": "Invalid or missing X-API-Key header"},
        422: {"description": "Invalid request body (missing required fields)"}
    }
)
async def start_backup(
    request: BackupStartRequest,
    db: AsyncSession = Depends(get_db)
):\n    \"\"\"Start a new backup session.
    \n    **Flow:**
    1. Device provides device_id and metadata
    2. Server creates session record
    3. Returns session_id for subsequent requests
    
    **Next:** Use session_id in /backup/manifest endpoint
    \"\"\"\n    service = BackupService(db)
    return await service.start_session(request)

@router.post(\n    \"/manifest\",
    response_model=ManifestResponse,
    summary=\"Check File Manifest (Delta Sync)\",
    description=\"Submit file hashes to identify missing files. Server responds with list of files that need uploading, enabling deduplication and bandwidth optimization.\",
    tags=[\"Backup\"],
    responses={
        200: {\"description\": \"Manifest processed successfully\"},
        401: {\"description\": \"Invalid or missing X-API-Key header\"},
        422: {\"description\": \"Invalid request body\"}
    }
)
async def check_manifest(
    request: ManifestRequest,
    db: AsyncSession = Depends(get_db)
):\n    \"\"\"Check which files are missing on the server.
    \n    **Key Benefits:**
    - **Deduplication:** Identifies files already stored
    - **Bandwidth Saving:** Only missing files need uploading
    - **Smart Sync:** Avoids re-uploading duplicate content
    
    **Next:** Upload only files in 'missing' list to /upload
    \"\"\"\n    service = BackupService(db)
    return await service.check_manifest(request)

@router.get(\n    \"/session/{session_id}\",
    response_model=SessionResponse,
    summary=\"Get Session Details\",
    description=\"Retrieve complete session information including progress metrics and timestamps.\",
    tags=[\"Backup\"],
    responses={
        200: {\"description\": \"Session details retrieved\"},
        401: {\"description\": \"Invalid or missing X-API-Key header\"},
        404: {\"description\": \"Session not found\"}
    }
)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):\n    \"\"\"Get complete session information.
    \n    **Returns:**
    - Session status and timestamps
    - Progress metrics (% complete)
    - File/byte counters
    \"\"\"\n    service = BackupService(db)
    return await service.get_session(session_id)

@router.delete(\n    \"/session/{session_id}\",
    response_model=SuccessResponse,
    summary=\"Delete Backup Session\",
    description=\"Remove session record. Note: Only metadata is deleted; uploaded files remain on server.\",
    tags=[\"Backup\"],
    responses={
        200: {\"description\": \"Session deleted successfully\"},
        401: {\"description\": \"Invalid or missing X-API-Key header\"},
        404: {\"description\": \"Session not found\"}
    }
)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):\n    \"\"\"Delete a backup session.
    \n    **Warning:** This deletes metadata only. Uploaded files remain.
    \"\"\"\n    service = BackupService(db)
    deleted = await service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=\"Session not found\")
    return SuccessResponse(message=\"Backup session deleted successfully\")"
