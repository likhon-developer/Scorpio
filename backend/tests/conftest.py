"""
Shared test fixtures and configuration
"""

import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis

from app.main import app
from app.core.config import settings

# Override settings for testing
settings.MONGODB_DATABASE = "test_db"
settings.REDIS_URL = "redis://localhost:6379/1"  # Use a different DB for testing

@pytest.fixture
def client() -> Generator:
    with TestClient(app) as test_client:
        yield test_client

@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator:
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest_asyncio.fixture
async def mongodb():
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    db = client[settings.MONGODB_DATABASE]
    yield db
    # Cleanup after tests
    await client.drop_database(settings.MONGODB_DATABASE)
    client.close()

@pytest_asyncio.fixture
async def redis_client():
    redis_client = redis.from_url(settings.REDIS_URL)
    yield redis_client
    # Cleanup after tests
    await redis_client.flushdb()
    await redis_client.close()

@pytest.fixture
def test_user():
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "name": "Test User"
    }

@pytest.fixture
def auth_headers(test_user):
    # Create a mock JWT token
    return {"Authorization": f"Bearer test-token-{test_user['id']}"}
