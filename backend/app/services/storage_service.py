import os
import hashlib
import time
import aiofiles
import uuid
from pathlib import Path
from fastapi import UploadFile
from app.core.config import get_settings, Settings
from app.core.security import get_media_subfolder
from app.core.logging import get_logger

logger = get_logger(__name__)

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    logger.warning("python-magic not installed. MIME detection will be less accurate.")

class StorageService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.base_path = Path(self.settings.UPLOAD_DIR)
        self.media_path = self.base_path / "media"
        self.images_path = self.media_path / "images"
        self.videos_path = self.media_path / "videos"
        self.thumbnails_path = self.base_path / "thumbnails"
        self.temp_path = self.base_path / "temp"
        self.logs_path = self.base_path / "logs"
        
    def ensure_directories(self) -> None:
        """Create all required storage directories."""
        for path in [self.images_path, self.videos_path, self.thumbnails_path, self.temp_path, self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage directories ensured at {self.base_path}")

    async def save_file_with_hash(self, file: UploadFile, original_filename: str) -> dict:
        """
        Save file while computing SHA256 and detecting MIME type in a single pass.
        
        Returns:
            {
                'upload_id': str (UUID),
                'stored_filename': str,
                'original_filename': str,
                'sha256': str,
                'mime_type': str,
                'size': int,
                'relative_path': str
            }
        """
        # Generate UUID for the file
        file_id = str(uuid.uuid4())
        # Get file extension from original filename
        _, ext = os.path.splitext(original_filename)
        stored_filename = f"{file_id}{ext}"
        
        sha256_hash = hashlib.sha256()
        total_size = 0
        chunk_size = self.settings.CHUNK_READ_SIZE
        
        # Prepare storage based on initial MIME type
        initial_mime = file.content_type or "application/octet-stream"
        subfolder = get_media_subfolder(initial_mime)
        dest_dir = self.media_path / subfolder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / stored_filename
        relative_path = f"media/{subfolder}/{stored_filename}"
        
        # Stream file to disk while computing hash and collecting bytes for MIME detection
        first_chunk = True
        magic_mime = None
        
        async with aiofiles.open(dest_path, "wb") as dest:
            while chunk := await file.read(chunk_size):
                # Compute hash
                sha256_hash.update(chunk)
                total_size += len(chunk)
                
                # Detect MIME type from first chunk using magic
                if first_chunk and HAS_MAGIC:
                    try:
                        magic_mime = magic.from_buffer(chunk, mime=True)
                        first_chunk = False
                    except Exception as e:
                        logger.warning(f"MIME detection failed: {e}")
                        magic_mime = initial_mime
                
                # Write to disk
                await dest.write(chunk)
        
        # Use detected MIME or fallback to client's content type
        final_mime = magic_mime or initial_mime
        
        logger.info(f"Saved file {stored_filename} ({total_size} bytes, SHA256: {sha256_hash.hexdigest()}, MIME: {final_mime})")
        
        return {
            'upload_id': file_id,
            'stored_filename': stored_filename,
            'original_filename': original_filename,
            'sha256': sha256_hash.hexdigest(),
            'mime_type': final_mime,
            'size': total_size,
            'relative_path': relative_path
        }
        
        
    async def save_file_streaming(self, file: UploadFile, stored_filename: str, mime_type: str) -> tuple[str, int]:
        """Stream file to disk in chunks. Returns (relative_path, file_size)."""
        subfolder = get_media_subfolder(mime_type)
        dest_dir = self.media_path / subfolder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / stored_filename
        relative_path = f"media/{subfolder}/{stored_filename}"
        
        total_size = 0
        chunk_size = self.settings.CHUNK_READ_SIZE
        
        async with aiofiles.open(dest_path, "wb") as dest:
            while chunk := await file.read(chunk_size):
                await dest.write(chunk)
                total_size += len(chunk)
                
        logger.info(f"Saved file {stored_filename} ({total_size} bytes) to {relative_path}")
        return relative_path, total_size

    async def save_thumbnail(self, file: UploadFile, stored_filename: str) -> str:
        """Save thumbnail file. Returns relative path."""
        thumb_name = f"thumb_{stored_filename}"
        dest_path = self.thumbnails_path / thumb_name
        relative_path = f"thumbnails/{thumb_name}"
        
        async with aiofiles.open(dest_path, "wb") as dest:
            while chunk := await file.read(self.settings.CHUNK_READ_SIZE):
                await dest.write(chunk)
                
        logger.info(f"Saved thumbnail {thumb_name} to {relative_path}")
        return relative_path

    async def compute_sha256(self, relative_path: str) -> str:
        """Compute SHA256 hash of a stored file."""
        full_path = self.get_full_path(relative_path)
        sha256_hash = hashlib.sha256()
        
        async with aiofiles.open(full_path, "rb") as f:
            while chunk := await f.read(self.settings.CHUNK_READ_SIZE):
                sha256_hash.update(chunk)
                
        return sha256_hash.hexdigest()

    def delete_file(self, relative_path: str) -> bool:
        """Delete a file by relative path. Returns True if deleted."""
        try:
            full_path = self.get_full_path(relative_path)
            if full_path.exists() and full_path.is_file():
                full_path.unlink()
                logger.info(f"Deleted file: {relative_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete file {relative_path}: {e}")
        return False

    def get_full_path(self, relative_path: str) -> Path:
        """Get absolute path from relative path, with traversal protection."""
        # Clean relative path to remove leading slash or backslash
        cleaned_path = relative_path.lstrip("/\\")
        full_path = (self.base_path / cleaned_path).resolve()
        # Ensure the resolved path is under the base path
        base_resolved = self.base_path.resolve()
        if not str(full_path).startswith(str(base_resolved)):
            raise ValueError(f"Path traversal detected: {relative_path}")
        return full_path

    def get_storage_stats(self) -> dict:
        """Calculate storage usage statistics."""
        stats = {
            "total_size_bytes": 0,
            "images_size_bytes": 0,
            "videos_size_bytes": 0,
            "thumbnails_size_bytes": 0,
            "temp_size_bytes": 0,
            "file_count": 0,
            "image_count": 0,
            "video_count": 0,
        }
        
        # Walk directories and accumulate sizes and counts
        for path, count_key, size_key in [
            (self.images_path, "image_count", "images_size_bytes"),
            (self.videos_path, "video_count", "videos_size_bytes"),
            (self.thumbnails_path, None, "thumbnails_size_bytes"),
            (self.temp_path, None, "temp_size_bytes"),
        ]:
            if path.exists():
                for entry in os.scandir(path):
                    if entry.is_file():
                        size = entry.stat().st_size
                        stats[size_key] += size
                        stats["total_size_bytes"] += size
                        if count_key:
                            stats[count_key] += 1
                            stats["file_count"] += 1
                            
        return stats

    def cleanup_temp(self, max_age_seconds: int = 3600) -> int:
        """Remove temp files older than max_age_seconds. Returns count of deleted files."""
        deleted = 0
        if not self.temp_path.exists():
            return 0
            
        now = time.time()
        for f in self.temp_path.iterdir():
            if f.is_file() and (now - f.stat().st_mtime) > max_age_seconds:
                try:
                    f.unlink()
                    deleted += 1
                except Exception as e:
                    logger.error(f"Failed to delete temp file {f}: {e}")
                    
        logger.info(f"Cleaned up {deleted} temp files from temp directory")
        return deleted

    def file_exists(self, relative_path: str) -> bool:
        try:
            full_path = self.get_full_path(relative_path)
            return full_path.exists() and full_path.is_file()
        except ValueError:
            return False

def get_storage_service() -> StorageService:
    return StorageService()
