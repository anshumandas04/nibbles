import datetime
from fastapi import UploadFile, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.device_repository import DeviceRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.log_repository import LogRepository
from app.services.storage_service import StorageService
from app.core.security import validate_mime_type, sanitize_filename, generate_stored_filename
from app.core.logging import get_logger
from app.core.config import get_settings
from app.models.models import MediaFile, UploadLog, FailedUpload
from app.schemas.upload import (
    UploadResponse, UploadFailureRequest, UploadStatusResponse, UploadSummary
)
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

    async def upload_file(
        self,
        file: UploadFile,
        device_id: str,
        sha256: str,
        mime_type: str,
        original_filename: str,
        session_id: str | None = None,
        created_time: str | None = None,
        thumbnail: UploadFile | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> UploadResponse:
        # 1. Look up or create device
        device = await self.device_repo.get_or_create(device_id)
        
        # 2. Validate MIME type
        if not validate_mime_type(mime_type):
            raise HTTPException(status_code=400, detail=f"MIME type '{mime_type}' is not allowed.")
            
        # 3. Check deduplication
        existing_file = await self.media_repo.find_by_sha256(sha256, device.id)
        if existing_file and existing_file.is_complete:
            # Create a log entry for the dedup hit
            log_entry = UploadLog(
                upload_id=existing_file.id,
                device_id=device.device_id,
                action="dedup_hit",
                details={"original_filename": original_filename, "sha256": sha256, "size": existing_file.file_size},
                ip_address=ip_address,
                user_agent=user_agent
            )
            await self.log_repo.create_log(log_entry)
            
            # If session is active, update progress
            if session_id:
                session = await self.session_repo.get_by_id(session_id)
                if session and session.status == "active":
                    session.uploaded_files += 1
                    session.uploaded_bytes += existing_file.file_size
                    
            logger.info(f"Deduplication hit for {original_filename} (SHA256: {sha256}) on device {device_id}")
            return UploadResponse(
                success=True,
                upload_id=existing_file.id,
                stored_filename=existing_file.stored_filename,
                sha256=sha256,
                size=existing_file.file_size,
                is_duplicate=True,
                created_at=existing_file.uploaded_time
            )

        # 4. Clean and prepare file names
        sanitized = sanitize_filename(original_filename)
        stored_name = generate_stored_filename(sanitized)
        
        # 5. Save the file to disk via streaming
        try:
            relative_path, total_size = await self.storage.save_file_streaming(file, stored_name, mime_type)
        except Exception as e:
            logger.error(f"Failed to stream upload for file {original_filename} to disk: {e}")
            raise HTTPException(status_code=500, detail="Failed to write file to storage.")

        # 6. Validate size limit
        if total_size > self.settings.max_upload_size_bytes:
            self.storage.delete_file(relative_path)
            raise HTTPException(status_code=413, detail=f"File exceeds maximum allowed size of {self.settings.MAX_UPLOAD_SIZE_MB}MB")

        # 7. Compute SHA256 of the stored file to verify integrity
        computed_sha = await self.storage.compute_sha256(relative_path)
        if computed_sha != sha256:
            self.storage.delete_file(relative_path)
            logger.error(f"Checksum mismatch for file {original_filename}: expected {sha256}, got {computed_sha}")
            raise HTTPException(status_code=409, detail="Checksum verification failed. The file may be corrupted.")

        # 8. Save thumbnail if provided
        thumb_path = None
        if thumbnail:
            try:
                thumb_path = await self.storage.save_thumbnail(thumbnail, stored_name)
            except Exception as e:
                logger.error(f"Failed to save thumbnail for {original_filename}: {e}")
                # Continue without failing the main upload

        # 9. Parse client file creation time
        parsed_created_time = None
        if created_time:
            try:
                # ISO format timestamp parsing
                parsed_created_time = datetime.datetime.fromisoformat(created_time.replace("Z", "+00:00"))
            except ValueError:
                pass

        # 10. Record MediaFile entry in database
        media_file = MediaFile(
            device_id=device.id,
            session_id=session_id,
            original_filename=sanitized,
            stored_filename=stored_name,
            relative_path=relative_path,
            mime_type=mime_type,
            file_size=total_size,
            sha256=sha256,
            thumbnail_path=thumb_path,
            media_path=str(self.storage.get_full_path(relative_path)),
            created_time=parsed_created_time,
            status="completed",
            is_complete=True
        )
        await self.media_repo.create(media_file)
        await self.db.flush()

        # 11. Create upload log record
        log_entry = UploadLog(
            upload_id=media_file.id,
            device_id=device.device_id,
            action="upload_completed",
            details={"original_filename": sanitized, "stored_filename": stored_name, "size": total_size},
            ip_address=ip_address,
            user_agent=user_agent
        )
        await self.log_repo.create_log(log_entry)

        # 12. Update active backup session if present
        if session_id:
            session = await self.session_repo.get_by_id(session_id)
            if session and session.status == "active":
                session.uploaded_files += 1
                session.uploaded_bytes += total_size

        return UploadResponse(
            success=True,
            upload_id=media_file.id,
            stored_filename=stored_name,
            sha256=sha256,
            size=total_size,
            is_duplicate=False,
            created_at=media_file.uploaded_time
        )

    async def report_failure(self, request: UploadFailureRequest) -> None:
        # Register device if it does not exist
        await self.device_repo.get_or_create(request.device_id)
        
        failure = FailedUpload(
            device_id=request.device_id,
            original_filename=request.original_filename,
            sha256=request.sha256,
            error_message=request.error_message
        )
        await self.log_repo.create_failure(failure)
        
        # Log to server logs as well
        logger.error(f"Device {request.device_id} reported upload failure for {request.original_filename}: {request.error_message}")

    async def get_upload_status(self, device_id: str) -> UploadStatusResponse:
        # Get device
        device = await self.device_repo.get_by_device_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
            
        # 1. Get active session if any
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
            
        # 2. Get recent media file uploads
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
        
        # 3. Get failed uploads count
        failed_count = await self.log_repo.count_failures_by_device(device_id)
        
        return UploadStatusResponse(
            device_id=device_id,
            active_session=active_sess_schema,
            recent_uploads=recent_uploads,
            failed_count=failed_count
        )
