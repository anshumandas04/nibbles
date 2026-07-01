import uuid
import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime, Text, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)

class Device(Base):
    __tablename__ = "devices"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    device_id: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    platform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    first_seen: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    sessions: Mapped[List["BackupSession"]] = relationship(back_populates="device", cascade="all, delete-orphan")
    media_files: Mapped[List["MediaFile"]] = relationship(back_populates="device", cascade="all, delete-orphan")


class BackupSession(Base):
    __tablename__ = "backup_sessions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, completed, failed, cancelled
    total_files: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_files: Mapped[int] = mapped_column(Integer, default=0)
    total_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    uploaded_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    
    device: Mapped["Device"] = relationship(back_populates="sessions")
    media_files: Mapped[List["MediaFile"]] = relationship(back_populates="session", cascade="all, delete-orphan")


class MediaFile(Base):
    __tablename__ = "media_files"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    device_id: Mapped[str] = mapped_column(String(36), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("backup_sessions.id", ondelete="SET NULL"), nullable=True, index=True)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    relative_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    media_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    created_time: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    uploaded_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    status: Mapped[str] = mapped_column(String(20), default="completed")  # completed, deleted
    is_complete: Mapped[bool] = mapped_column(Boolean, default=True)
    
    device: Mapped["Device"] = relationship(back_populates="media_files")
    session: Mapped[Optional["BackupSession"]] = relationship(back_populates="media_files")
    upload_logs: Mapped[List["UploadLog"]] = relationship(back_populates="media_file", cascade="all, delete-orphan")


class UploadLog(Base):
    __tablename__ = "upload_logs"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    upload_id: Mapped[Optional[str]] = mapped_column(String(36), ForeignKey("media_files.id", ondelete="SET NULL"), nullable=True, index=True)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # upload_started, upload_completed, upload_failed, dedup_hit, deleted
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    
    media_file: Mapped[Optional["MediaFile"]] = relationship(back_populates="upload_logs")


class FailedUpload(Base):
    __tablename__ = "failed_uploads"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    sha256: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

# Composite Index for dedup
Index("ix_media_files_device_sha256", MediaFile.device_id, MediaFile.sha256)
