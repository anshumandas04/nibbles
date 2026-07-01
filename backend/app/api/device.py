from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.core.security import verify_api_key
from app.services.device_service import DeviceService
from app.schemas.device import DeviceSyncResponse

router = APIRouter(
    prefix="/device",
    tags=["Device"],
    dependencies=[Depends(verify_api_key)]
)

@router.get("/sync", response_model=DeviceSyncResponse)
async def get_device_sync_status(
    device_id: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db)
):
    service = DeviceService(db)
    return await service.get_sync_status(device_id)
