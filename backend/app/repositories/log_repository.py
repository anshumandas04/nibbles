from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.models import UploadLog, FailedUpload
import datetime

class LogRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        
    async def create_log(self, log: UploadLog) -> UploadLog:
        self.db.add(log)
        await self.db.flush()
        return log
        
    async def get_recent_logs(self, limit: int = 50) -> list[UploadLog]:
        result = await self.db.execute(
            select(UploadLog)
            .order_by(UploadLog.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
        
    async def create_failure(self, failure: FailedUpload) -> FailedUpload:
        self.db.add(failure)
        await self.db.flush()
        return failure
        
    async def count_failures_by_device(self, device_id: str) -> int:
        result = await self.db.execute(
            select(func.count(FailedUpload.id)).where(FailedUpload.device_id == device_id)
        )
        return result.scalar_one()
        
    async def get_recent_failures(self, limit: int = 10) -> list[FailedUpload]:
        result = await self.db.execute(
            select(FailedUpload)
            .order_by(FailedUpload.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_failures_all(self) -> int:
        result = await self.db.execute(
            select(func.count(FailedUpload.id))
        )
        return result.scalar_one()
