import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.repositories.device_repository import DeviceRepository
from app.repositories.media_repository import MediaRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.log_repository import LogRepository
from app.services.storage_service import StorageService
from app.models.models import UploadLog, Device
from app.core.config import get_settings

SERVER_START_TIME = None

def set_server_start_time() -> None:
    global SERVER_START_TIME
    if SERVER_START_TIME is None:
        SERVER_START_TIME = time.time()

def get_uptime() -> str:
    if SERVER_START_TIME is None:
        return "unknown"
    elapsed = time.time() - SERVER_START_TIME
    days = int(elapsed // 86400)
    hours = int((elapsed % 86400) // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    return " ".join(parts)

class DashboardService:
    def __init__(self, db: AsyncSession, storage: StorageService) -> None:
        self.db = db
        self.storage = storage
        self.device_repo = DeviceRepository(db)
        self.media_repo = MediaRepository(db)
        self.session_repo = SessionRepository(db)
        self.log_repo = LogRepository(db)

    async def get_dashboard_data(self) -> dict:
        settings = get_settings()
        
        # 1. Total uploads count & total storage size from database
        total_uploads = await self.media_repo.count_all()
        total_storage_bytes = await self.media_repo.total_size()
        
        # 2. Get storage stats from disk (images vs videos vs thumbnails vs temp)
        disk_stats = self.storage.get_storage_stats()
        
        # 3. Calculate deduplication savings from logs
        dedup_result = await self.db.execute(
            select(UploadLog).where(UploadLog.action == "dedup_hit")
        )
        dedup_logs = dedup_result.scalars().all()
        dedup_savings_bytes = sum(int(log.details.get("size", 0)) for log in dedup_logs if log.details)
        
        # 4. Recent lists
        recent_uploads_raw = await self.media_repo.get_recent(limit=10)
        recent_uploads = []
        for r in recent_uploads_raw:
            # Get device identifier for display
            device = await self.db.get(Device, r.device_id)
            device_lbl = device.name or device.device_id if device else "Unknown"
            recent_uploads.append({
                "id": r.id,
                "original_filename": r.original_filename,
                "stored_filename": r.stored_filename,
                "mime_type": r.mime_type,
                "file_size": r.file_size,
                "sha256": r.sha256,
                "status": r.status,
                "uploaded_time": r.uploaded_time,
                "device_label": device_lbl
            })
            
        recent_sessions_raw = await self.session_repo.get_recent(limit=5)
        recent_sessions = []
        for s in recent_sessions_raw:
            device = await self.db.get(Device, s.device_id)
            device_lbl = device.name or device.device_id if device else "Unknown"
            progress = 0.0
            if s.total_files > 0:
                progress = round((s.uploaded_files / s.total_files) * 100, 2)
            recent_sessions.append({
                "id": s.id,
                "device_label": device_lbl,
                "started_at": s.started_at,
                "completed_at": s.completed_at,
                "status": s.status,
                "total_files": s.total_files,
                "uploaded_files": s.uploaded_files,
                "total_bytes": s.total_bytes,
                "uploaded_bytes": s.uploaded_bytes,
                "progress_percent": progress
            })

        recent_failures_raw = await self.log_repo.get_recent_failures(limit=5)
        recent_failures = [
            {
                "id": f.id,
                "device_id": f.device_id,
                "original_filename": f.original_filename,
                "sha256": f.sha256,
                "error_message": f.error_message,
                "created_at": f.created_at
            }
            for f in recent_failures_raw
        ]

        recent_logs_raw = await self.log_repo.get_recent_logs(limit=20)
        recent_logs = [
            {
                "id": l.id,
                "device_id": l.device_id,
                "action": l.action,
                "details": l.details,
                "ip_address": l.ip_address,
                "created_at": l.created_at
            }
            for l in recent_logs_raw
        ]

        # 5. Global failures count
        failed_count = await self.log_repo.count_failures_all()
        
        # 6. Current uploading status: check if there's any active backup sessions
        active_sessions_result = await self.db.execute(
            select(func.count(Device.id)).join(Device.sessions).where(Device.sessions.any(status="active"))
        )
        active_devices_count = active_sessions_result.scalar_one()

        return {
            "total_uploads": total_uploads,
            "total_storage_bytes": total_storage_bytes,
            "recent_uploads": recent_uploads,
            "recent_sessions": recent_sessions,
            "recent_failures": recent_failures,
            "storage_stats": disk_stats,
            "recent_logs": recent_logs,
            "server_uptime": get_uptime(),
            "failed_count": failed_count,
            "dedup_savings_bytes": dedup_savings_bytes,
            "active_devices_count": active_devices_count,
            "app_name": settings.APP_NAME,
            "version": settings.BUILD_VERSION
        }
