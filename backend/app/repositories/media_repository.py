"""Media file repository for database CRUD operations on MediaFile model.

Handles media file record creation, lookup, deduplication checks,
pagination, and aggregate queries for storage statistics.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import MediaFile


class MediaRepository:
    """Repository class encapsulating all database operations for the MediaFile model."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository with an async database session.

        Args:
            db: SQLAlchemy async session instance.
        """
        self.db = db

    async def find_by_sha256(self, sha256: str, device_id: str) -> MediaFile | None:
        """Find an existing media file by its SHA-256 hash for a specific device.

        Used for deduplication: if a file with the same hash already exists
        for this device, there is no need to re-upload it.

        Args:
            sha256: The SHA-256 hex digest of the file content.
            device_id: The internal device UUID (primary key).

        Returns:
            The MediaFile instance if found, otherwise None.
        """
        result = await self.db.execute(
            select(MediaFile).where(
                MediaFile.sha256 == sha256,
                MediaFile.device_id == device_id,
            )
        )
        return result.scalar_one_or_none()

    async def find_by_sha256_any(self, sha256: str) -> MediaFile | None:
        """Find an existing media file by its SHA-256 hash globally (any device).

        Used for global deduplication across all devices/users.

        Args:
            sha256: The SHA-256 hex digest of the file content.

        Returns:
            The MediaFile instance if found, otherwise None.
        """
        result = await self.db.execute(
            select(MediaFile).where(
                MediaFile.sha256 == sha256,
                MediaFile.is_complete.is_(True),
            ).limit(1)
        )
        return result.scalar_one_or_none()


    async def find_existing_hashes(
        self, sha256_list: list[str], device_id: str
    ) -> set[str]:
        """Batch-check which SHA-256 hashes already exist for a device.

        Used during manifest checking to determine which files the client
        can skip uploading.

        Args:
            sha256_list: List of SHA-256 hex digests to check.
            device_id: The internal device UUID (primary key).

        Returns:
            Set of SHA-256 strings that already exist in the database.
        """
        if not sha256_list:
            return set()

        result = await self.db.execute(
            select(MediaFile.sha256).where(
                MediaFile.sha256.in_(sha256_list),
                MediaFile.device_id == device_id,
                MediaFile.is_complete.is_(True),
            )
        )
        return {row[0] for row in result.all()}

    async def create(self, media_file: MediaFile) -> MediaFile:
        """Insert a new media file record into the database.

        Args:
            media_file: The MediaFile instance to persist.

        Returns:
            The persisted MediaFile instance with generated fields populated.
        """
        self.db.add(media_file)
        await self.db.flush()
        return media_file

    async def get_by_id(self, media_id: str) -> MediaFile | None:
        """Retrieve a media file by its primary key.

        Args:
            media_id: The UUID primary key of the media file.

        Returns:
            The MediaFile instance if found, otherwise None.
        """
        result = await self.db.execute(
            select(MediaFile).where(MediaFile.id == media_id)
        )
        return result.scalar_one_or_none()

    async def list_by_device(
        self, device_id: str, page: int, page_size: int
    ) -> tuple[list[MediaFile], int]:
        """Retrieve a paginated list of media files for a specific device.

        Args:
            device_id: The internal device UUID (primary key).
            page: The 1-indexed page number.
            page_size: Number of records per page.

        Returns:
            Tuple of (list of MediaFile records, total count).
        """
        offset = (page - 1) * page_size

        count_result = await self.db.execute(
            select(func.count(MediaFile.id)).where(
                MediaFile.device_id == device_id
            )
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(MediaFile)
            .where(MediaFile.device_id == device_id)
            .order_by(MediaFile.uploaded_time.desc())
            .offset(offset)
            .limit(page_size)
        )
        files = list(result.scalars().all())

        return files, total

    async def list_all(
        self, page: int, page_size: int
    ) -> tuple[list[MediaFile], int]:
        """Retrieve a paginated list of all media files.

        Args:
            page: The 1-indexed page number.
            page_size: Number of records per page.

        Returns:
            Tuple of (list of MediaFile records, total count).
        """
        offset = (page - 1) * page_size

        count_result = await self.db.execute(
            select(func.count(MediaFile.id))
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(MediaFile)
            .order_by(MediaFile.uploaded_time.desc())
            .offset(offset)
            .limit(page_size)
        )
        files = list(result.scalars().all())

        return files, total

    async def count_by_device(self, device_id: str) -> int:
        """Count the number of media files for a specific device.

        Args:
            device_id: The internal device UUID (primary key).

        Returns:
            The total number of media files for the device.
        """
        result = await self.db.execute(
            select(func.count(MediaFile.id)).where(
                MediaFile.device_id == device_id
            )
        )
        return result.scalar_one()

    async def total_size_by_device(self, device_id: str) -> int:
        """Calculate total storage used by a specific device.

        Args:
            device_id: The internal device UUID (primary key).

        Returns:
            Total bytes stored for the device, or 0 if none.
        """
        result = await self.db.execute(
            select(func.coalesce(func.sum(MediaFile.file_size), 0)).where(
                MediaFile.device_id == device_id
            )
        )
        return result.scalar_one()

    async def get_recent(self, limit: int = 10) -> list[MediaFile]:
        """Retrieve the most recently uploaded media files.

        Args:
            limit: Maximum number of records to return (default 10).

        Returns:
            List of the most recent MediaFile records, ordered by upload time descending.
        """
        result = await self.db.execute(
            select(MediaFile)
            .order_by(MediaFile.uploaded_time.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete(self, media_id: str) -> MediaFile | None:
        """Delete a media file record by its primary key.

        The record is returned before deletion so the caller can perform
        cleanup of the associated files on disk.

        Args:
            media_id: The UUID primary key of the media file to delete.

        Returns:
            The deleted MediaFile instance, or None if not found.
        """
        media_file = await self.get_by_id(media_id)
        if media_file is None:
            return None
        await self.db.delete(media_file)
        await self.db.flush()
        return media_file

    async def count_all(self) -> int:
        """Count all media files in the database.

        Returns:
            Total number of media file records.
        """
        result = await self.db.execute(
            select(func.count(MediaFile.id))
        )
        return result.scalar_one()

    async def total_size(self) -> int:
        """Calculate total storage used across all devices.

        Returns:
            Total bytes stored, or 0 if no files exist.
        """
        result = await self.db.execute(
            select(func.coalesce(func.sum(MediaFile.file_size), 0))
        )
        return result.scalar_one()
