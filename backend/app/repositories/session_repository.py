"""Backup session repository for database CRUD operations on BackupSession model.

Handles session lifecycle: creation, progress tracking, completion, and lookup.
"""

import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import BackupSession


class SessionRepository:
    """Repository class encapsulating all database operations for the BackupSession model."""

    def __init__(self, db: AsyncSession) -> None:
        """Initialize repository with an async database session.

        Args:
            db: SQLAlchemy async session instance.
        """
        self.db = db

    async def create(self, session: BackupSession) -> BackupSession:
        """Insert a new backup session record.

        Args:
            session: The BackupSession instance to persist.

        Returns:
            The persisted BackupSession instance with generated fields populated.
        """
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_by_id(self, session_id: str) -> BackupSession | None:
        """Retrieve a backup session by its primary key.

        Args:
            session_id: The UUID primary key of the session.

        Returns:
            The BackupSession instance if found, otherwise None.
        """
        result = await self.db.execute(
            select(BackupSession).where(BackupSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_device(self, device_id: str) -> BackupSession | None:
        """Retrieve the currently active backup session for a device.

        A device should have at most one active session at any time.

        Args:
            device_id: The internal device UUID (primary key from devices table).

        Returns:
            The active BackupSession if one exists, otherwise None.
        """
        result = await self.db.execute(
            select(BackupSession).where(
                BackupSession.device_id == device_id,
                BackupSession.status == "active",
            )
        )
        return result.scalar_one_or_none()

    async def update_progress(
        self, session_id: str, uploaded_files: int, uploaded_bytes: int
    ) -> None:
        """Increment the progress counters for a backup session.

        This uses absolute values, not increments, so callers must track
        the running totals themselves or query before updating.

        Args:
            session_id: The UUID primary key of the session.
            uploaded_files: New total count of uploaded files.
            uploaded_bytes: New total count of uploaded bytes.
        """
        session = await self.get_by_id(session_id)
        if session:
            session.uploaded_files = uploaded_files
            session.uploaded_bytes = uploaded_bytes

    async def complete(self, session_id: str) -> None:
        """Mark a backup session as completed.

        Sets the status to 'completed' and records the completion timestamp.

        Args:
            session_id: The UUID primary key of the session.
        """
        session = await self.get_by_id(session_id)
        if session:
            session.status = "completed"
            session.completed_at = datetime.datetime.now(datetime.timezone.utc)

    async def delete(self, session_id: str) -> BackupSession | None:
        """Delete a backup session record.

        Args:
            session_id: The UUID primary key of the session to delete.

        Returns:
            The deleted BackupSession instance, or None if not found.
        """
        session = await self.get_by_id(session_id)
        if session is None:
            return None
        await self.db.delete(session)
        await self.db.flush()
        return session

    async def get_recent(self, limit: int = 10) -> list[BackupSession]:
        """Retrieve the most recent backup sessions.

        Args:
            limit: Maximum number of records to return (default 10).

        Returns:
            List of BackupSession records ordered by start time descending.
        """
        result = await self.db.execute(
            select(BackupSession)
            .order_by(BackupSession.started_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_last_completed_by_device(
        self, device_id: str
    ) -> BackupSession | None:
        """Retrieve the most recently completed backup session for a device.

        Args:
            device_id: The internal device UUID (primary key from devices table).

        Returns:
            The most recent completed BackupSession, or None if no completed sessions exist.
        """
        result = await self.db.execute(
            select(BackupSession)
            .where(
                BackupSession.device_id == device_id,
                BackupSession.status == "completed",
            )
            .order_by(BackupSession.completed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
