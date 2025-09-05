"""
Test suite for chat endpoints
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
async def test_create_chat_session(async_client):
    response = await async_client.post("/api/v1/chat/sessions", json={
        "name": "Test Session",
        "description": "Test chat session"
    })
    assert response.status_code == 201
    data = response.json()
    assert "session_id" in data
    assert data["name"] == "Test Session"

@pytest.mark.asyncio
async def test_get_chat_sessions(async_client):
    response = await async_client.get("/api/v1/chat/sessions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

@pytest.mark.asyncio
async def test_send_message(async_client):
    # First create a session
    session_response = await async_client.post("/api/v1/chat/sessions", json={
        "name": "Test Session",
        "description": "Test chat session"
    })
    session_id = session_response.json()["session_id"]
    
    # Send a message
    response = await async_client.post(f"/api/v1/chat/sessions/{session_id}/messages", json={
        "content": "Hello, AI!",
        "type": "user"
    })
    assert response.status_code == 201
    data = response.json()
    assert "message_id" in data
    assert data["content"] == "Hello, AI!"

@pytest.mark.asyncio
async def test_get_chat_history(async_client):
    # First create a session
    session_response = await async_client.post("/api/v1/chat/sessions", json={
        "name": "Test Session",
        "description": "Test chat session"
    })
    session_id = session_response.json()["session_id"]
    
    # Get chat history
    response = await async_client.get(f"/api/v1/chat/sessions/{session_id}/messages")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
