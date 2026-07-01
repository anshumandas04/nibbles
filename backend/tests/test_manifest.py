import pytest
import hashlib

@pytest.mark.asyncio
async def test_manifest_delta_sync(client, api_headers):
    # 1. Start session
    session_response = await client.post(
        "/backup/start",
        headers=api_headers,
        json={
            "device_id": "manifest-device",
            "total_files": 5,
            "total_bytes": 500
        }
    )
    session_id = session_response.json()["session_id"]
    
    # 2. Upload file 1
    file1_content = b"first file data"
    file1_sha256 = hashlib.sha256(file1_content).hexdigest()
    file1_size = len(file1_content)
    
    upload_response = await client.post(
        "/upload",
        headers=api_headers,
        files={"file": ("file1.png", file1_content, "image/png")},
        data={
            "device_id": "manifest-device",
            "sha256": file1_sha256,
            "mime_type": "image/png",
            "original_filename": "file1.png",
            "session_id": session_id
        }
    )
    assert upload_response.status_code == 200
    
    # 3. Call manifest checking
    # File 1 has been uploaded (exists). File 2 and File 3 are new (missing).
    file2_sha256 = "c" * 64
    file3_sha256 = "d" * 64
    
    manifest_response = await client.post(
        "/backup/manifest",
        headers=api_headers,
        json={
            "device_id": "manifest-device",
            "session_id": session_id,
            "files": [
                {"sha256": file1_sha256, "size": file1_size, "filename": "file1.png", "mime_type": "image/png"},
                {"sha256": file2_sha256, "size": 150, "filename": "file2.png", "mime_type": "image/png"},
                {"sha256": file3_sha256, "size": 250, "filename": "file3.png", "mime_type": "image/png"}
            ]
        }
    )
    assert manifest_response.status_code == 200
    manifest_data = manifest_response.json()
    assert manifest_data["total_received"] == 3
    assert manifest_data["already_exists"] == 1
    assert manifest_data["bytes_saved"] == file1_size
    assert set(manifest_data["missing"]) == {file2_sha256, file3_sha256}
