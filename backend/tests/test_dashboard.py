import pytest

@pytest.mark.asyncio
async def test_dashboard_unauthorized(client):
    response = await client.get("/dashboard")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_dashboard_authorized(client):
    response = await client.get("/dashboard?key=test-api-key")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "").lower()
    
    html_content = response.text
    assert "<html" in html_content.lower()
    assert "cloudsync backup" in html_content.lower()
