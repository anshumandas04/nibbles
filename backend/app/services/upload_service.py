import datetime
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.device_repository import DeviceRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.log_repository import LogRepository
from app.services.storage_service import StorageService
from app.core.security import validate_mime_type
from app.core.logging import get_logger
from app.core.config import get_settings
from app.models.models import MediaFile, UploadLog
from app.schemas.upload import UploadStatusResponse, UploadSummary
from app.schemas.backup import SessionResponse

logger = get_logger(__name__)

class UploadService:
    def __init__(self, db: AsyncSession, storage: StorageService) -> None:
        self.db = db
        self.storage = storage
        self.device_repo = DeviceRepository(db)
        self.session_repo = SessionRepository(db)
        self.media_repo = MediaRepository(db)
        self.log_repo = LogRepository(db)
        self.settings = get_settings()

    async def check_duplicate(self, sha256: str) -> MediaFile | None:
        """Check if a file with this SHA256 already exists (deduplication)."""
        existing = await self.media_repo.find_by_sha256_any(sha256)
        return existing if existing and existing.is_complete else None

    async def save_file_metadata(
        self,
        upload_id: str,
        device_id: str,
        session_id: str | None,
        original_filename: str,
        stored_filename: str,
        sha256: str,
        mime_type: str,
        size: int,
        relative_path: str,
        created_time: datetime.datetime | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> MediaFile:
        """Save file metadata to database after successful upload."""
        # Get or create device
        device = await self.device_repo.get_or_create(device_id)
        
        # Validate MIME type
        if not validate_mime_type(mime_type):
            logger.warning(f"Unsupported MIME type: {mime_type}")
            # Still allow it, but log a warning
        
        # Create MediaFile record
        media_file = MediaFile(
            id=upload_id,
            device_id=device.id,
            session_id=session_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            relative_path=relative_path,
            mime_type=mime_type,
            file_size=size,
            sha256=sha256,
            media_path=str(self.storage.get_full_path(relative_path)),
            created_time=created_time,
            status="completed",
            is_complete=True
        )
        await self.media_repo.create(media_file)
        await self.db.flush()
        
        # Create upload log record
        log_entry = UploadLog(
            upload_id=upload_id,
            device_id=device.device_id,
            action="upload_completed",
            details={
                "original_filename": original_filename,
                "stored_filename": stored_filename,
                "size": size,
                "mime_type": mime_type
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        await self.log_repo.create_log(log_entry)
        
        # Update active backup session if present
        if session_id:
            session = await self.session_repo.get_by_id(session_id)
            if session and session.status == "active":
                session.uploaded_files += 1
                session.uploaded_bytes += size
        
        logger.info(f"Saved file metadata for {original_filename} (SHA256: {sha256}, size: {size})")
        return media_file

    async def get_upload_status(self, device_id: str) -> UploadStatusResponse:
        """Get upload status for a device."""
        # Get device
        device = await self.device_repo.get_by_device_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
            
        # Get active session if any
        active_sess = await self.session_repo.get_active_by_device(device.id)
        active_sess_schema = None
        if active_sess:
            progress = 0.0
            if active_sess.total_files > 0:
                progress = round((active_sess.uploaded_files / active_sess.total_files) * 100, 2)
            active_sess_schema = SessionResponse(
                id=active_sess.id,
                device_id=active_sess.device_id,
                started_at=active_sess.started_at,
                completed_at=active_sess.completed_at,
                status=active_sess.status,
                total_files=active_sess.total_files,
                uploaded_files=active_sess.uploaded_files,
                total_bytes=active_sess.total_bytes,
                uploaded_bytes=active_sess.uploaded_bytes,
                progress_percent=progress
            )
            
        # Get recent media file uploads
        files, _ = await self.media_repo.list_by_device(device.id, page=1, page_size=10)
        recent_uploads = [
            UploadSummary(
                id=f.id,
                original_filename=f.original_filename,
                size=f.file_size,
                status=f.status,
                uploaded_time=f.uploaded_time
            )
            for f in files
        ]
        
        return UploadStatusResponse(
            device_id=device_id,
            active_session=active_sess_schema,
            recent_uploads=recent_uploads,
            failed_count=0
        )

