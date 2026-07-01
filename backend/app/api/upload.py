from fastapi import APIRouter, Depends, UploadFile, File, Form, Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.core.security import verify_api_key
from app.services.upload_service import UploadService
from app.services.storage_service import StorageService, get_storage_service
from app.schemas.upload import (
    UploadResponse, UploadCompleteRequest, UploadCompleteResponse,
    UploadFailureRequest, UploadStatusResponse
)
from app.schemas.common import SuccessResponse
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/upload",
    tags=["Upload"],
    dependencies=[Depends(verify_api_key)]
)

@router.post("", response_model=UploadResponse)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    thumbnail: UploadFile | None = File(None),
    device_id: str = Form(...),
    sha256: str = Form(...),
    mime_type: str = Form(...),
    original_filename: str = Form(...),
    session_id: str | None = Form(None),
    created_time: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    service = UploadService(db, storage)
    return await service.upload_file(
        file=file,
        thumbnail=thumbnail,
        device_id=device_id,
        sha256=sha256,
        mime_type=mime_type,
        original_filename=original_filename,
        session_id=session_id,
        created_time=created_time,
        ip_address=ip_address,
        user_agent=user_agent
    )

@router.post("/complete", response_model=UploadCompleteResponse)
async def complete_upload(
    request: UploadCompleteRequest,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    # Retrieve the file record
    from app.repositories.media_repository import MediaRepository
    media_repo = MediaRepository(db)
    
    media_file = await media_repo.get_by_id(request.upload_id)
    if not media_file:
        raise HTTPException(status_code=404, detail="Upload record not found")
        
    # Verify the hash of the stored file
    computed_sha = await storage.compute_sha256(media_file.relative_path)
    verified = (computed_sha == request.sha256)
    
    if not verified:
        logger.error(f"Integrity check failed on complete for upload {request.upload_id}. Expected {request.sha256}, got {computed_sha}")
        # Update media status to failed
        media_file.status = "failed"
        media_file.is_complete = False
        message = "SHA256 verification failed on server"
    else:
        media_file.status = "completed"
        media_file.is_complete = True
        message = "Verification successful"
        
    return UploadCompleteResponse(
        success=verified,
        upload_id=request.upload_id,
        verified=verified,
        message=message
    )

@router.post("/failure", response_model=SuccessResponse)
async def report_failure(
    request: UploadFailureRequest,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    service = UploadService(db, storage)
    await service.report_failure(request)
    return SuccessResponse(message="Failure report recorded")

@router.get("/status/{device_id}", response_model=UploadStatusResponse)
async def get_upload_status(
    device_id: str,
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    service = UploadService(db, storage)
    return await service.get_upload_status(device_id)
