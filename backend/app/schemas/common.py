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
        example="InvalidInput\""
    )
    detail: Optional[str] = Field(
        None,
        description="Detailed error message",
        example=\"Field 'device_id' is required\"\n    )\n\nclass HealthResponse(BaseModel):\n    \"\"\"Server health check response.\"\"\"\n    status: str = Field(\n        ...,\n        description=\"Overall server status\",\n        example=\"ok\"\n    )\n    database: str = Field(\n        ...,\n        description=\"Database connection status\",\n        example=\"connected\"\n    )\n    storage: str = Field(\n        ...,\n        description=\"Storage system status\",\n        example=\"available\"\n    )\n    timestamp: datetime = Field(\n        ...,\n        description=\"Health check timestamp\",\n        example=\"2026-07-02T10:30:45.123Z\"\n    )\n\nclass VersionResponse(BaseModel):\n    \"\"\"Application version information.\"\"\"\n    app_name: str = Field(\n        ...,\n        description=\"Application name\",\n        example=\"CloudSync Backup\"\n    )\n    version: str = Field(\n        ...,\n        description=\"Application version\",\n        example=\"1.0.0\"\n    )\n    timestamp: datetime = Field(\n        ...,\n        description=\"Response timestamp\",\n        example=\"2026-07-02T10:30:45.123Z"
