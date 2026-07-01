"""initial migration

Revision ID: 001
Revises: None
Create Date: 2026-06-30 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create devices table
    op.create_table(
        'devices',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('device_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('platform', sa.String(length=50), nullable=True),
        sa.Column('first_seen', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_devices_device_id'), 'devices', ['device_id'], unique=True)

    # 2. Create backup_sessions table
    op.create_table(
        'backup_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('device_id', sa.String(length=36), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('total_files', sa.Integer(), nullable=False),
        sa.Column('uploaded_files', sa.Integer(), nullable=False),
        sa.Column('total_bytes', sa.BigInteger(), nullable=False),
        sa.Column('uploaded_bytes', sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_backup_sessions_device_id'), 'backup_sessions', ['device_id'], unique=False)

    # 3. Create media_files table
    op.create_table(
        'media_files',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('device_id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=True),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('stored_filename', sa.String(length=255), nullable=False),
        sa.Column('relative_path', sa.String(length=1000), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=False),
        sa.Column('thumbnail_path', sa.String(length=1000), nullable=True),
        sa.Column('media_path', sa.String(length=1000), nullable=False),
        sa.Column('created_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('uploaded_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('is_complete', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['backup_sessions.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stored_filename')
    )
    op.create_index(op.f('ix_media_files_device_id'), 'media_files', ['device_id'], unique=False)
    op.create_index(op.f('ix_media_files_session_id'), 'media_files', ['session_id'], unique=False)
    op.create_index(op.f('ix_media_files_sha256'), 'media_files', ['sha256'], unique=False)
    # Compound index for dedup
    op.create_index('ix_media_files_device_sha256', 'media_files', ['device_id', 'sha256'], unique=False)

    # 4. Create upload_logs table
    op.create_table(
        'upload_logs',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('upload_id', sa.String(length=36), nullable=True),
        sa.Column('device_id', sa.String(length=255), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('details', sa.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['upload_id'], ['media_files.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_upload_logs_device_id'), 'upload_logs', ['device_id'], unique=False)
    op.create_index(op.f('ix_upload_logs_upload_id'), 'upload_logs', ['upload_id'], unique=False)

    # 5. Create failed_uploads table
    op.create_table(
        'failed_uploads',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('device_id', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=500), nullable=False),
        sa.Column('sha256', sa.String(length=64), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('last_attempt', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_failed_uploads_device_id'), 'failed_uploads', ['device_id'], unique=False)
    op.create_index(op.f('ix_failed_uploads_sha256'), 'failed_uploads', ['sha256'], unique=False)


def downgrade() -> None:
    op.drop_table('failed_uploads')
    op.drop_table('upload_logs')
    op.drop_table('media_files')
    op.drop_table('backup_sessions')
    op.drop_table('devices')
