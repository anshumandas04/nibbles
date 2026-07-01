from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.device_repository import DeviceRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.session_repository import SessionRepository
from app.schemas.device import DeviceSyncResponse

class DeviceService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.device_repo = DeviceRepository(db)
        self.media_repo = MediaRepository(db)
        self.session_repo = SessionRepository(db)

    async def get_sync_status(self, device_id: str) -> DeviceSyncResponse:
        device = await self.device_repo.get_by_device_id(device_id)
        if not device:
            raise HTTPException(status_code=404, detail=f"Device '{device_id}' is not registered.")

        uploaded_count = await self.media_repo.count_by_device(device.id)
        total_size = await self.media_repo.total_size_by_device(device.id)
        
        last_completed = await self.session_repo.get_last_completed_by_device(device.id)
        last_backup_time = last_completed.completed_at if last_completed else None
        
        # Calculate remaining files if there's an active session
        remaining = 0
        active_session = await self.session_repo.get_active_by_device(device.id)
        if active_session:
            remaining = max(0, active_session.total_files - active_session.uploaded_files)

        return DeviceSyncResponse(
            device_id=device_id,
            last_backup=last_backup_time,
            uploaded_count=uploaded_count,
            total_size_bytes=total_size,
            remaining=remaining,
            last_seen=device.last_seen
        )
