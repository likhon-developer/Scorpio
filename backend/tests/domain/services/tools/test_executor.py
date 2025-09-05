"""
Tests for the tool execution service with parallel processing.
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from typing import Dict, Any

from app.domain.services.tools.executor import ToolExecutor, ToolResult
from app.core.exceptions import ToolExecutionError

# Test data
SAMPLE_SESSION_ID = "test_session_123"
SAMPLE_TOOL_NAME = "test_tool"
SAMPLE_PARAMETERS = {"param1": "value1"}

@pytest.fixture
def mock_session_service():
    service = Mock()
    service.get_session.return_value = Mock(tool_executions=[])
    service.update_session.return_value = None
    return service

@pytest.fixture
def mock_redis():
    redis = Mock()
    redis.get.return_value = None
    redis.set.return_value = True
    return redis

@pytest.fixture
def mock_db():
    db = Mock()
    db.tool_results = Mock()
    db.tool_results.insert_one.return_value = None
    return db

@pytest.fixture
def tool_executor(mock_session_service, mock_redis, mock_db):
    executor = ToolExecutor(
        session_service=mock_session_service,
        redis=mock_redis,
        db=mock_db,
        max_workers=2,
        max_retries=2,
        rate_limit=5
    )
    
    async def mock_execute_tool(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        return {"result": "success"}
    
    executor._execute_tool = mock_execute_tool
    return executor

@pytest.mark.asyncio
async def test_execute_tool_success(tool_executor):
    """Test successful tool execution."""
    result = await tool_executor.execute(
        SAMPLE_SESSION_ID,
        SAMPLE_TOOL_NAME,
        SAMPLE_PARAMETERS
    )
    
    assert isinstance(result, ToolResult)
    assert result.status == "completed"
    assert result.tool_name == SAMPLE_TOOL_NAME
    assert result.parameters == SAMPLE_PARAMETERS
    assert result.result == {"result": "success"}
    assert result.error is None
    assert result.retries == 0

@pytest.mark.asyncio
async def test_execute_tool_with_retry(tool_executor):
    """Test tool execution with retry on failure."""
    fail_count = 0
    
    async def failing_execute_tool(tool_name: str, parameters: Dict[str, Any]):
        nonlocal fail_count
        if fail_count < 1:
            fail_count += 1
            raise Exception("Temporary failure")
        return {"result": "success after retry"}
    
    tool_executor._execute_tool = failing_execute_tool
    
    result = await tool_executor.execute(
        SAMPLE_SESSION_ID,
        SAMPLE_TOOL_NAME,
        SAMPLE_PARAMETERS
    )
    
    assert result.status == "completed"
    assert result.retries == 1
    assert result.result == {"result": "success after retry"}

@pytest.mark.asyncio
async def test_execute_batch_parallel(tool_executor):
    """Test parallel execution of multiple tools."""
    tools = [
        (SAMPLE_TOOL_NAME, SAMPLE_PARAMETERS),
        (SAMPLE_TOOL_NAME, {"param2": "value2"}),
        (SAMPLE_TOOL_NAME, {"param3": "value3"})
    ]
    
    results = await tool_executor.execute_batch(
        SAMPLE_SESSION_ID,
        tools,
        parallel=True
    )
    
    assert len(results) == 3
    assert all(r.status == "completed" for r in results)
    assert len({r.created_at for r in results}) > 1  # Verify parallel execution

@pytest.mark.asyncio
async def test_execute_batch_sequential(tool_executor):
    """Test sequential execution of multiple tools."""
    tools = [
        (SAMPLE_TOOL_NAME, SAMPLE_PARAMETERS),
        (SAMPLE_TOOL_NAME, {"param2": "value2"})
    ]
    
    results = await tool_executor.execute_batch(
        SAMPLE_SESSION_ID,
        tools,
        parallel=False
    )
    
    assert len(results) == 2
    assert all(r.status == "completed" for r in results)
    timestamps = [r.created_at for r in results]
    assert timestamps[0] < timestamps[1]  # Verify sequential execution

@pytest.mark.asyncio
async def test_rate_limiting(tool_executor):
    """Test rate limiting of tool executions."""
    tools = [(SAMPLE_TOOL_NAME, SAMPLE_PARAMETERS) for _ in range(10)]
    
    start_time = datetime.now(timezone.utc)
    results = await tool_executor.execute_batch(
        SAMPLE_SESSION_ID,
        tools,
        parallel=True
    )
    end_time = datetime.now(timezone.utc)
    
    assert len(results) == 10
    duration = (end_time - start_time).total_seconds()
    assert duration >= 1  # Rate limiting should prevent instant completion

@pytest.mark.asyncio
async def test_caching(tool_executor, mock_redis):
    """Test result caching."""
    cached_result = ToolResult(
        tool_name=SAMPLE_TOOL_NAME,
        parameters=SAMPLE_PARAMETERS,
        result={"cached": "value"},
        status="completed",
        duration=0.1
    )
    mock_redis.get.return_value = cached_result.json()
    
    result = await tool_executor.execute(
        SAMPLE_SESSION_ID,
        SAMPLE_TOOL_NAME,
        SAMPLE_PARAMETERS
    )
    
    assert result.result == {"cached": "value"}
    mock_redis.get.assert_called_once()
