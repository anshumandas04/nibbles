import os
import secrets
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.services.storage_service import StorageService, get_storage_service
from app.services.dashboard_service import DashboardService
from app.core.config import get_settings

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
async def get_dashboard(
    request: Request,
    key: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage_service)
):
    settings = get_settings()
    
    # Check for API key in query parameter or header
    api_key_header = request.headers.get("X-API-Key")
    api_key = key or api_key_header
    
    if not api_key or not secrets.compare_digest(api_key, settings.API_KEY):
        raise HTTPException(
            status_code=401, 
            detail="Unauthorized. Please provide a valid X-API-Key header or '?key=YOUR_API_KEY' query parameter."
        )
        
    service = DashboardService(db, storage)
    data = await service.get_dashboard_data()
    
    # Context must contain 'request'
    context = {"request": request, **data}
    return templates.TemplateResponse("dashboard.html", context)
