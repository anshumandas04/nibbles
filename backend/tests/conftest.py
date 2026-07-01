import pytest
import asyncio
import os
from httpx import AsyncClient, ASGITransport
from pathlib import Path

# 1. Set environment variables BEFORE importing app
os.environ["API_KEY"] = "test-api-key"
os.environ["SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["UPLOAD_DIR"] = "test_storage"
os.environ["LOG_LEVEL"] = "DEBUG"
os.environ["MAX_UPLOAD_SIZE_MB"] = "10"
os.environ["RATE_LIMIT"] = "1000/minute"

from app.database.database import Base, reset_engine, get_engine
from app.core.config import get_settings
from main import app  # noqa

TEST_API_KEY = "test-api-key"

@pytest.fixture(autouse=True)
async def setup_database(tmp_path):
    """Create fresh database and mock storage directories for each test."""
    # Set the upload directory for testing to a temp directory
    test_storage = tmp_path / "test_storage"
    for subdir in ["media/images", "media/videos", "thumbnails", "temp", "logs"]:
        (test_storage / subdir).mkdir(parents=True, exist_ok=True)
        
    os.environ["UPLOAD_DIR"] = str(test_storage)
    
    # Clear settings cache so new UPLOAD_DIR is picked up
    get_settings.cache_clear()
    
    # Reset engine to pick up new DATABASE_URL/settings
    reset_engine()
    
    # Create all tables in sqlite in-memory
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        
    await engine.dispose()
    reset_engine()

@pytest.fixture
async def client():
    """Async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def api_headers():
    return {"X-API-Key": TEST_API_KEY}

@pytest.fixture
def storage_dir(tmp_path):
    """Create and return temp storage directory path."""
    return tmp_path / "test_storage"
