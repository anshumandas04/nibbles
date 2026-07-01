import pytest
import hashlib

@pytest.mark.asyncio
async def test_media_catalog_endpoints(client, api_headers):
    # 1. Initially, media list should be empty (or at least we can verify pagination format)
    list_response = await client.get("/media", headers=api_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 0

    # 2. Upload a media file
    file_content = b"0123456789abcdefghijklmnopqrstuvwxyz" # 36 bytes
    sha256 = hashlib.sha256(file_content).hexdigest()
    
    upload_response = await client.post(
        "/upload",
        headers=api_headers,
        files={"file": ("alphabet.txt", file_content, "application/octet-stream")},
        data={
            "device_id": "media-device",
            "sha256": sha256,
            "mime_type": "application/octet-stream",
            "original_filename": "alphabet.txt"
        }
    )
    assert upload_response.status_code == 200
    media_id = upload_response.json()["upload_id"]

    # 3. List media again and verify it's there
    list_response = await client.get("/media", headers=api_headers)
    assert list_response.status_code == 200
    list_data = list_response.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["id"] == media_id

    # 4. Get specific media details
    details_response = await client.get(f"/media/{media_id}", headers=api_headers)
    assert details_response.status_code == 200
    assert details_response.json()["original_filename"] == "alphabet.txt"

    # 5. Download the file completely
    download_response = await client.get(f"/download/{media_id}", headers=api_headers)
    assert download_response.status_code == 200
    assert download_response.content == file_content

    # 6. Download the file with Range header (resumable restore)
    # Get bytes 0 to 9 (10 bytes)
    range_headers = {"Range": "bytes=0-9", **api_headers}
    range_response = await client.get(f"/download/{media_id}", headers=range_headers)
    assert range_response.status_code == 206
    assert range_response.content == b"0123456789"
    assert range_response.headers["Content-Range"] == "bytes 0-9/36"

    # Get bytes 10 to 19 (10 bytes)
    range_headers2 = {"Range": "bytes=10-19", **api_headers}
    range_response2 = await client.get(f"/download/{media_id}", headers=range_headers2)
    assert range_response2.status_code == 206
    assert range_response2.content == b"abcdefghij"
    assert range_response2.headers["Content-Range"] == "bytes 10-19/36"

    # 7. Delete media file
    delete_response = await client.delete(f"/media/{media_id}", headers=api_headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["success"] is True

    # 8. Check that file returns 404 details
    details_response_after = await client.get(f"/media/{media_id}", headers=api_headers)
    assert details_response_after.status_code == 404
