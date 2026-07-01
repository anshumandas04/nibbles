"""Security utilities — API key verification, filename sanitisation, MIME validation."""

import os
import re
import secrets
import uuid

from fastapi import Depends, Header, HTTPException

from app.core.config import Settings, get_settings

ALLOWED_MIME_TYPES: set[str] = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/heic",
    "image/heif",
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
    "video/3gpp",
    "application/octet-stream",
}


async def verify_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"),
    settings: Settings = Depends(get_settings),
) -> str:
    """FastAPI dependency that validates the ``X-API-Key`` header.

    Uses constant-time comparison to prevent timing attacks.
    """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
    if not secrets.compare_digest(x_api_key, settings.API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


def generate_stored_filename(original_filename: str) -> str:
    """Generate a UUID-based filename preserving the original extension.

    Example
    -------
    >>> generate_stored_filename("photo.JPG")
    'a1b2c3d4e5f6...jpg'
    """
    ext = get_safe_extension(original_filename)
    return f"{uuid.uuid4().hex}{ext}"


def get_safe_extension(filename: str) -> str:
    """Extract and sanitise a file extension.

    Only alphanumeric extensions are allowed; everything else is stripped.
    """
    _, ext = os.path.splitext(filename)
    if ext and re.match(r"^\.[a-zA-Z0-9]+$", ext):
        return ext.lower()
    return ""


def sanitize_filename(filename: str) -> str:
    """Remove path-traversal characters and dangerous sequences."""
    filename = os.path.basename(filename)
    filename = re.sub(r"[^\w\s\-.]", "", filename)
    filename = filename.strip(". ")
    return filename or "unnamed"


def validate_mime_type(mime_type: str) -> bool:
    """Return ``True`` if *mime_type* is in the allow-list."""
    return mime_type.lower() in ALLOWED_MIME_TYPES


def validate_file_size(size: int, max_size: int) -> bool:
    """Return ``True`` if *size* is within the acceptable range."""
    return 0 < size <= max_size


def is_image_mime(mime_type: str) -> bool:
    """Check whether *mime_type* denotes an image."""
    return mime_type.lower().startswith("image/")


def is_video_mime(mime_type: str) -> bool:
    """Check whether *mime_type* denotes a video."""
    return mime_type.lower().startswith("video/")


def get_media_subfolder(mime_type: str) -> str:
    """Return ``'images'``, ``'videos'``, or ``'other'`` based on MIME type."""
    if is_image_mime(mime_type):
        return "images"
    if is_video_mime(mime_type):
        return "videos"
    return "other"
