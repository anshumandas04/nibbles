from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.media_repository import MediaRepository
from app.repositories.log_repository import LogRepository
from app.repositories.device_repository import DeviceRepository
from app.services.storage_service import StorageService
from app.models.models import UploadLog
from app.schemas.media import MediaFileResponse, MediaListResponse
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)

class MediaService:
    def __init__(self, db: AsyncSession, storage: StorageService) -> None:
        self.db = db
        self.storage = storage
        self.media_repo = MediaRepository(db)
        self.log_repo = LogRepository(db)
        self.device_repo = DeviceRepository(db)

    async def list_media(self, page: int = 1, page_size: int = 20, device_id: str | None = None) -> MediaListResponse:
        if device_id:
            device = await self.device_repo.get_by_device_id(device_id)
            if not device:
                return MediaListResponse(items=[], total=0, page=page, page_size=page_size)
            files, total = await self.media_repo.list_by_device(device.id, page, page_size)
        else:
            files, total = await self.media_repo.list_all(page, page_size)

        items = [
            MediaFileResponse(
                id=f.id,
                device_id=f.device_id,
                session_id=f.session_id,
                original_filename=f.original_filename,
                stored_filename=f.stored_filename,
                mime_type=f.mime_type,
                file_size=f.file_size,
                sha256=f.sha256,
                thumbnail_path=f.thumbnail_path,
                status=f.status,
                is_complete=f.is_complete,
                uploaded_time=f.uploaded_time,
                created_time=f.created_time
            )
            for f in files
        ]
        return MediaListResponse(items=items, total=total, page=page, page_size=page_size)

    async def get_media(self, media_id: str) -> MediaFileResponse:
        f = await self.media_repo.get_by_id(media_id)
        if not f:
            raise HTTPException(status_code=404, detail="Media file not found")
            
        return MediaFileResponse(
            id=f.id,
            device_id=f.device_id,
            session_id=f.session_id,
            original_filename=f.original_filename,
            stored_filename=f.stored_filename,
            mime_type=f.mime_type,
            file_size=f.file_size,
            sha256=f.sha256,
            thumbnail_path=f.thumbnail_path,
            status=f.status,
            is_complete=f.is_complete,
            uploaded_time=f.uploaded_time,
            created_time=f.created_time
        )

    async def get_download_path(self, media_id: str) -> Path:
        f = await self.media_repo.get_by_id(media_id)
        if not f:
            raise HTTPException(status_code=404, detail="Media file not found")
            
        # Verify file actually exists on disk
        if not self.storage.file_exists(f.relative_path):
            logger.error(f"File database entry exists for {media_id} but actual file is missing on disk: {f.relative_path}")
            raise HTTPException(status_code=404, detail="Media file content is missing on disk.")
            
        return self.storage.get_full_path(f.relative_path)

    async def delete_media(self, media_id: str) -> bool:
        # Delete from DB
        f = await self.media_repo.delete(media_id)
        if not f:
            return False
            
        # Delete from disk
        self.storage.delete_file(f.relative_path)
        if f.thumbnail_path:
            self.storage.delete_file(f.thumbnail_path)
            
        # Log deletion
        log_entry = UploadLog(
            upload_id=None,
            device_id=f.device_id,
            action="deleted",
            details={"original_filename": f.original_filename, "stored_filename": f.stored_filename, "sha256": f.sha256},
            ip_address=None,
            user_agent=None
        )
        await self.log_repo.create_log(log_entry)
        
        logger.info(f"Deleted media record and file for upload_id={media_id}")
        return True
