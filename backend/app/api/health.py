from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import datetime
from app.database.database import get_db
from app.services.storage_service import StorageService, get_storage_service
from app.schemas.common import HealthResponse, VersionResponse
from app.core.config import get_settings

router = APIRouter(tags=["Health"])

@router.get("/")
async def root():
    settings = get_settings()
    return {
        "message": f"Welcome to the {settings.APP_NAME} API",
        "docs": "/docs",
        "status": "online"
    }

@router.get("/health", response_model=HealthResponse)
async def health(
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    # 1. Check database connection
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        
    # 2. Check storage accessibility
    try:
        # Try to check if storage directory is writable
        storage.ensure_directories()
        storage_status = "healthy"
    except Exception as e:
        storage_status = f"unhealthy: {str(e)}"
        
    # 3. Overall status
    overall = "healthy" if db_status == "healthy" and storage_status == "healthy" else "degraded"
    
    return HealthResponse(
        status=overall,
        database=db_status,
        storage=storage_status,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )

@router.get("/version", response_model=VersionResponse)
async def version():
    settings = get_settings()
    return VersionResponse(
        app_name=settings.APP_NAME,
        version=settings.BUILD_VERSION,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
    )
