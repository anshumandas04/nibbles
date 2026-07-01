from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.core.security import verify_api_key
from app.services.media_service import MediaService
from app.services.storage_service import StorageService, get_storage_service
from app.repositories.media_repository import MediaRepository

router = APIRouter(
    prefix="/download",
    tags=["Download"],
    dependencies=[Depends(verify_api_key)]
)

@router.get("/{media_id}")
async def download_file(
    media_id: str,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    media_repo = MediaRepository(db)
    media_file = await media_repo.get_by_id(media_id)
    if not media_file:
        raise HTTPException(status_code=404, detail="Media file not found")
        
    service = MediaService(db, storage)
    full_path = await service.get_download_path(media_id)
    
    # FileResponse handles range headers automatically in FastAPI/Starlette
    return FileResponse(
        path=str(full_path),
        media_type=media_file.mime_type,
        filename=media_file.original_filename
    )
