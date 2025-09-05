"""
Test suite for file handling endpoints
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
import pytest_asyncio
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_upload_file(async_client):
    # Create a test file
    file_content = b"Test file content"
    files = {"file": ("test.txt", file_content, "text/plain")}
    
    response = await async_client.post(
        "/api/v1/files/upload",
        files=files
    )
    assert response.status_code == 201
    data = response.json()
    assert "file_id" in data
    assert data["filename"] == "test.txt"

@pytest.mark.asyncio
async def test_get_file_info(async_client):
    # First upload a file
    file_content = b"Test file content"
    files = {"file": ("test.txt", file_content, "text/plain")}
    upload_response = await async_client.post("/api/v1/files/upload", files=files)
    file_id = upload_response.json()["file_id"]
    
    # Get file info
    response = await async_client.get(f"/api/v1/files/{file_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["file_id"] == file_id
    assert data["filename"] == "test.txt"

@pytest.mark.asyncio
async def test_list_files(async_client):
    response = await async_client.get("/api/v1/files")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_delete_file(async_client):
    # First upload a file
    file_content = b"Test file content"
    files = {"file": ("test.txt", file_content, "text/plain")}
    upload_response = await async_client.post("/api/v1/files/upload", files=files)
    file_id = upload_response.json()["file_id"]
    
    # Delete the file
    response = await async_client.delete(f"/api/v1/files/{file_id}")
    assert response.status_code == 204
    
    # Verify file is deleted
    get_response = await async_client.get(f"/api/v1/files/{file_id}")
    assert get_response.status_code == 404
