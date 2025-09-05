"""
Test suite for AI tools endpoints
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
async def test_list_available_tools(async_client):
    response = await async_client.get("/api/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    
    # Verify tool schema
    tool = data[0]
    assert "id" in tool
    assert "name" in tool
    assert "description" in tool
    assert "parameters" in tool

@pytest.mark.asyncio
async def test_execute_tool(async_client):
    # Test executing a simple tool (e.g., text analysis)
    response = await async_client.post("/api/v1/tools/execute", json={
        "tool_id": "text-analysis",
        "parameters": {
            "text": "Sample text for analysis"
        }
    })
    assert response.status_code == 200
    data = response.json()
    assert "result" in data

@pytest.mark.asyncio
async def test_get_tool_execution_history(async_client):
    response = await async_client.get("/api/v1/tools/history")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_get_tool_status(async_client):
    # First start a tool execution
    execution_response = await async_client.post("/api/v1/tools/execute", json={
        "tool_id": "text-analysis",
        "parameters": {
            "text": "Sample text for analysis"
        }
    })
    execution_id = execution_response.json()["execution_id"]
    
    # Get status
    response = await async_client.get(f"/api/v1/tools/status/{execution_id}")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["completed", "running", "failed"]

@pytest.mark.asyncio
async def test_invalid_tool_execution(async_client):
    response = await async_client.post("/api/v1/tools/execute", json={
        "tool_id": "non-existent-tool",
        "parameters": {}
    })
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_invalid_tool_parameters(async_client):
    response = await async_client.post("/api/v1/tools/execute", json={
        "tool_id": "text-analysis",
        "parameters": {}  # Missing required parameter
    })
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
