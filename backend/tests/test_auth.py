import pytest

@pytest.mark.asyncio
async def test_auth_missing_key(client):
    # Call a protected endpoint without key
    response = await client.post("/backup/start", json={})
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"

@pytest.mark.asyncio
async def test_auth_invalid_key(client):
    # Call protected endpoint with invalid key
    response = await client.post(
        "/backup/start", 
        headers={"X-API-Key": "invalid-key"},
        json={}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"

@pytest.mark.asyncio
async def test_auth_valid_key(client):
    # Call protected endpoint with valid key
    # It should not fail with 401 (might fail with 422 if body is invalid, but not 401)
    response = await client.post(
        "/backup/start", 
        headers={"X-API-Key": "test-api-key"},
        json={
            "device_id": "test-device",
            "device_name": "iPhone 15",
            "platform": "ios",
            "total_files": 10,
            "total_bytes": 1000
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["status"] == "active"
