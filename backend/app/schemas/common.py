from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional


class SuccessResponse(BaseModel):
    """Generic success response with optional data payload."""
    success: bool = Field(
        True,
        description="Always True for success responses"
    )
    message: str = Field(
        "OK",
        description="Human-readable success message",
        example="Operation completed successfully"
    )
    data: Optional[Any] = Field(
        None,
        description="Optional response data"
    )


class ErrorResponse(BaseModel):
    """Generic error response."""
    success: bool = Field(
        False,
        description="Always False for error responses"
    )
    error: str = Field(
        ...,
        description="Error type/code",
        example="InvalidInput"
    )
    detail: Optional[str] = Field(
        None,
        description="Detailed error message",
        example="Field 'device_id' is required"
    )


class HealthResponse(BaseModel):
    """Server health check response."""
    status: str = Field(
        ...,
        description="Overall server status",
        example="ok"
    )
    database: str = Field(
        ...,
        description="Database connection status",
        example="connected"
    )
    storage: str = Field(
        ...,
        description="Storage system status",
        example="available"
    )
    timestamp: datetime = Field(
        ...,
        description="Health check timestamp",
        example="2026-07-02T10:30:45.123Z"
    )


class VersionResponse(BaseModel):
    """Application version information."""
    app_name: str = Field(
        ...,
        description="Application name",
        example="CloudSync Backup"
    )
    version: str = Field(
        ...,
        description="Application version",
        example="1.0.0"
    )
    timestamp: datetime = Field(
        ...,
        description="Response timestamp",
        example="2026-07-02T10:30:45.123Z"
    )"
