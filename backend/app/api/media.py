from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.core.security import verify_api_key
from app.services.media_service import MediaService
from app.services.storage_service import StorageService, get_storage_service
from app.schemas.media import MediaFileResponse, MediaListResponse
from app.schemas.common import SuccessResponse

router = APIRouter(
    prefix="/media",
    tags=["Media"],
    dependencies=[Depends(verify_api_key)]
)

@router.get("", response_model=MediaListResponse)
async def list_media(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    device_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    service = MediaService(db, storage)
    return await service.list_media(page, page_size, device_id)

@router.get("/{media_id}", response_model=MediaFileResponse)
async def get_media_details(
    media_id: str,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    service = MediaService(db, storage)
    return await service.get_media(media_id)

@router.delete("/{media_id}", response_model=SuccessResponse)
async def delete_media(
    media_id: str,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    service = MediaService(db, storage)
    deleted = await service.delete_media(media_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Media file not found")
    return SuccessResponse(message="Media file and record deleted successfully")
