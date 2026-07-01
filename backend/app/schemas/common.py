from pydantic import BaseModel
from datetime import datetime
from typing import Any, Optional

class SuccessResponse(BaseModel):
    success: bool = True
    message: str = "OK"
    data: Optional[Any] = None

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    detail: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    database: str
    storage: str
    timestamp: datetime

class VersionResponse(BaseModel):
    app_name: str
    version: str
    timestamp: datetime
