from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.device_repository import DeviceRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.log_repository import LogRepository
from app.models.models import BackupSession
from app.schemas.backup import (
    BackupStartRequest, BackupStartResponse,
    ManifestRequest, ManifestResponse, SessionResponse
)
import datetime

class BackupService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.device_repo = DeviceRepository(db)
        self.session_repo = SessionRepository(db)
        self.media_repo = MediaRepository(db)
        self.log_repo = LogRepository(db)
        
    async def start_session(self, request: BackupStartRequest) -> BackupStartResponse:
        # 1. Register/get device
        device = await self.device_repo.get_or_create(
            device_id=request.device_id,
            name=request.device_name,
            platform=request.platform
        )
        
        # 2. Deactivate any existing active sessions to keep it clean (optional but good practice)
        active_session = await self.session_repo.get_active_by_device(device.id)
        if active_session:
            active_session.status = "failed"
            active_session.completed_at = datetime.datetime.now(datetime.timezone.utc)
            
        # 3. Create a new backup session
        session = BackupSession(
            device_id=device.id,
            status="active",
            total_files=request.total_files,
            total_bytes=request.total_bytes,
            uploaded_files=0,
            uploaded_bytes=0
        )
        
        await self.session_repo.create(session)
        await self.db.flush()
        
        return BackupStartResponse(
            session_id=session.id,
            device_id=request.device_id,
            status=session.status,
            started_at=session.started_at
        )
        
    async def check_manifest(self, request: ManifestRequest) -> ManifestResponse:
        # 1. Look up device
        device = await self.device_repo.get_by_device_id(request.device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not registered")
            
        # 2. Extract hashes from request
        sha256_list = [entry.sha256 for entry in request.files]
        if not sha256_list:
            return ManifestResponse(
                total_received=0,
                already_exists=0,
                missing=[],
                bytes_saved=0
            )
            
        # 3. Batch look up existing hashes in repository
        existing_hashes = await self.media_repo.find_existing_hashes(sha256_list, device.id)
        
        # 4. Filter missing files and calculate savings
        missing = []
        bytes_saved = 0
        already_exists_count = 0
        
        for entry in request.files:
            if entry.sha256 in existing_hashes:
                already_exists_count += 1
                bytes_saved += entry.size
            else:
                missing.append(entry.sha256)
                
        return ManifestResponse(
            total_received=len(request.files),
            already_exists=already_exists_count,
            missing=missing,
            bytes_saved=bytes_saved
        )
        
    async def get_session(self, session_id: str) -> SessionResponse:
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
            
        progress = 0.0
        if session.total_files > 0:
            progress = round((session.uploaded_files / session.total_files) * 100, 2)
            
        return SessionResponse(
            id=session.id,
            device_id=session.device_id,
            started_at=session.started_at,
            completed_at=session.completed_at,
            status=session.status,
            total_files=session.total_files,
            uploaded_files=session.uploaded_files,
            total_bytes=session.total_bytes,
            uploaded_bytes=session.uploaded_bytes,
            progress_percent=progress
        )
        
    async def delete_session(self, session_id: str) -> bool:
        session = await self.session_repo.delete(session_id)
        return session is not None
