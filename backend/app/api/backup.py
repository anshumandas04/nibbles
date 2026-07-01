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

@router.post("/start", response_model=BackupStartResponse)
async def start_backup(
    request: BackupStartRequest,
    db: AsyncSession = Depends(get_db)
):
    service = BackupService(db)
    return await service.start_session(request)

@router.post("/manifest", response_model=ManifestResponse)
async def check_manifest(
    request: ManifestRequest,
    db: AsyncSession = Depends(get_db)
):
    service = BackupService(db)
    return await service.check_manifest(request)

@router.get("/session/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    service = BackupService(db)
    return await service.get_session(session_id)

@router.delete("/session/{session_id}", response_model=SuccessResponse)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    service = BackupService(db)
    deleted = await service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")
    return SuccessResponse(message="Backup session deleted successfully")
