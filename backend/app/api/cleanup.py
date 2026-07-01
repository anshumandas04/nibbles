from fastapi import APIRouter, Depends, Query
from app.core.security import verify_api_key
from app.services.storage_service import StorageService, get_storage_service
from app.schemas.common import SuccessResponse

router = APIRouter(
    prefix="/cleanup",
    tags=["Cleanup"],
    dependencies=[Depends(verify_api_key)]
)

@router.post("/temp", response_model=SuccessResponse)
async def cleanup_temp_files(
    max_age_seconds: int = Query(3600, ge=0),
    storage: StorageService = Depends(get_storage_service)
):
    deleted_count = storage.cleanup_temp(max_age_seconds)
    return SuccessResponse(
        message=f"Temporary files cleanup completed successfully.",
        data={"deleted_count": deleted_count}
    )
