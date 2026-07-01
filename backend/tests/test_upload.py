import pytest
import hashlib
import io

@pytest.mark.asyncio
async def test_upload_lifecycle(client, api_headers):
    # 1. Start a backup session
    session_response = await client.post(
        "/backup/start",
        headers=api_headers,
        json={
            "device_id": "device-123",
            "device_name": "Pixel 7",
            "platform": "android",
            "total_files": 2,
            "total_bytes": 100
        }
    )
    assert session_response.status_code == 200
    session_id = session_response.json()["session_id"]

    # 2. Prepare file upload
    file_content = b"simulate image file content bytes"
    sha256 = hashlib.sha256(file_content).hexdigest()
    
    files = {
        "file": ("photo.jpg", file_content, "image/jpeg")
    }
    data = {
        "device_id": "device-123",
        "sha256": sha256,
        "mime_type": "image/jpeg",
        "original_filename": "photo.jpg",
        "session_id": session_id,
        "created_time": "2026-06-30T10:00:00Z"
    }

    # 3. Upload file
    upload_response = await client.post(
        "/upload",
        headers=api_headers,
        files=files,
        data=data
    )
    assert upload_response.status_code == 200
    upload_data = upload_response.json()
    assert upload_data["success"] is True
    assert upload_data["sha256"] == sha256
    assert upload_data["is_duplicate"] is False
    upload_id = upload_data["upload_id"]

    # 4. Upload the same file again (dedup check)
    # Reset file read pointer by sending another payload
    files_dup = {
        "file": ("photo.jpg", file_content, "image/jpeg")
    }
    upload_response_dup = await client.post(
        "/upload",
        headers=api_headers,
        files=files_dup,
        data=data
    )
    assert upload_response_dup.status_code == 200
    assert upload_response_dup.json()["is_duplicate"] is True
    assert upload_response_dup.json()["upload_id"] == upload_id

    # 5. Call complete endpoint to verify integrity
    complete_response = await client.post(
        "/upload/complete",
        headers=api_headers,
        json={
            "upload_id": upload_id,
            "sha256": sha256
        }
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["verified"] is True

    # 6. Check upload status
    status_response = await client.get(
        "/upload/status/device-123",
        headers=api_headers
    )
    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["device_id"] == "device-123"
    assert status_data["active_session"]["id"] == session_id
    assert len(status_data["recent_uploads"]) >= 1

@pytest.mark.asyncio
async def test_upload_invalid_mime(client, api_headers):
    file_content = b"some executable script data"
    sha256 = hashlib.sha256(file_content).hexdigest()
    
    files = {
        "file": ("malicious.sh", file_content, "application/x-sh")
    }
    data = {
        "device_id": "device-123",
        "sha256": sha256,
        "mime_type": "application/x-sh",
        "original_filename": "malicious.sh"
    }
    
    response = await client.post(
        "/upload",
        headers=api_headers,
        files=files,
        data=data
    )
    assert response.status_code == 400
    assert "not allowed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_checksum_mismatch(client, api_headers):
    file_content = b"correct image data"
    wrong_sha256 = "a" * 64
    
    files = {
        "file": ("image.jpg", file_content, "image/jpeg")
    }
    data = {
        "device_id": "device-123",
        "sha256": wrong_sha256,
        "mime_type": "image/jpeg",
        "original_filename": "image.jpg"
    }
    
    response = await client.post(
        "/upload",
        headers=api_headers,
        files=files,
        data=data
    )
    assert response.status_code == 409
    assert "verification failed" in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_failure_reporting(client, api_headers):
    # Report a failed upload
    response = await client.post(
        "/upload/failure",
        headers=api_headers,
        json={
            "device_id": "device-123",
            "original_filename": "broken_video.mp4",
            "sha256": "b" * 64,
            "error_message": "Network timeout during transfer"
        }
    )
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Retrieve status and verify failure is counted
    status_response = await client.get(
        "/upload/status/device-123",
        headers=api_headers
    )
    assert status_response.status_code == 200
    assert status_response.json()["failed_count"] == 1
