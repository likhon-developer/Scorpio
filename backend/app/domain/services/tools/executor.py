"""
Tool execution service with parallel processing support.

This module provides a service for executing tools with:
- Parallel execution capabilities
- Rate limiting
- Retry logic
- Result caching
- Error handling
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
import asyncio
from concurrent.futures import ThreadPoolExecutor
import structlog
from pydantic import BaseModel
from redis import asyncio as aioredis
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.domain.models.base.models import TimestampedModel, ParallelProcessingMixin
from app.core.exceptions import ToolExecutionError

logger = structlog.get_logger(__name__)

class ToolResult(TimestampedModel):
    """Model for tool execution results."""
    
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    duration: float
    status: str = "pending"  # pending, running, completed, failed
    retries: int = 0


class ToolExecutor(ParallelProcessingMixin):
    """Service for parallel tool execution."""

    def __init__(
        self,
        session_service: Any,
        redis: aioredis.Redis,
        db: AsyncIOMotorDatabase,
        max_workers: int = 4,
        max_retries: int = 3,
        rate_limit: int = 10
    ):
        super().__init__(max_workers=max_workers)
        self.session_service = session_service
        self.redis = redis
        self.db = db
        self.max_retries = max_retries
        self._rate_limiter = asyncio.Semaphore(rate_limit)
        self.results_collection = db.tool_results

    async def execute(
        self,
        session_id: str,
        tool_name: str,
        parameters: Dict[str, Any],
        cache_ttl: int = 300
    ) -> Dict[str, Any]:
        """Execute a tool with caching and retry logic."""
        cache_key = f"tool:{tool_name}:{hash(str(parameters))}"
        
        # Check cache first
        if cached := await self.redis.get(cache_key):
            return ToolResult.parse_raw(cached)

        async with self._rate_limiter:
            result = await self._execute_with_retry(
                session_id,
                tool_name,
                parameters
            )

            # Cache successful results
            if result.status == "completed":
                await self.redis.set(
                    cache_key,
                    result.json(),
                    ex=cache_ttl
                )

            return result

    async def execute_batch(
        self,
        session_id: str,
        tools: List[Tuple[str, Dict[str, Any]]],
        parallel: bool = True
    ) -> List[ToolResult]:
        """Execute multiple tools in parallel or sequence."""
        if parallel:
            return await self._execute_parallel(session_id, tools)
        else:
            return await self._execute_sequential(session_id, tools)

    async def _execute_with_retry(
        self,
        session_id: str,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> ToolResult:
        """Execute a tool with automatic retries."""
        start_time = datetime.now(timezone.utc)
        result = ToolResult(
            tool_name=tool_name,
            parameters=parameters,
            created_at=start_time
        )

        for attempt in range(self.max_retries):
            try:
                result.status = "running"
                await self._record_execution(session_id, result)
                
                tool_result = await self._execute_tool(tool_name, parameters)
                
                end_time = datetime.now(timezone.utc)
                result.status = "completed"
                result.result = tool_result
                result.duration = (end_time - start_time).total_seconds()
                await self._record_execution(session_id, result)
                
                return result

            except Exception as e:
                logger.error(
                    "Tool execution failed",
                    session_id=session_id,
                    tool_name=tool_name,
                    attempt=attempt + 1,
                    error=str(e)
                )
                result.retries += 1
                result.error = str(e)
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    result.status = "failed"
                    await self._record_execution(session_id, result)
                    raise ToolExecutionError(
                        f"Tool {tool_name} failed after {self.max_retries} attempts: {str(e)}"
                    )

    async def _execute_parallel(
        self,
        session_id: str,
        tools: List[Tuple[str, Dict[str, Any]]]
    ) -> List[ToolResult]:
        """Execute multiple tools in parallel."""
        async def execute_one(tool_info: Tuple[str, Dict[str, Any]]) -> ToolResult:
            tool_name, parameters = tool_info
            return await self.execute(session_id, tool_name, parameters)

        return await asyncio.gather(*[
            execute_one(tool_info) for tool_info in tools
        ])

    async def _execute_sequential(
        self,
        session_id: str,
        tools: List[Tuple[str, Dict[str, Any]]]
    ) -> List[ToolResult]:
        """Execute multiple tools sequentially."""
        results = []
        for tool_name, parameters in tools:
            result = await self.execute(session_id, tool_name, parameters)
            results.append(result)
        return results

    async def _record_execution(
        self,
        session_id: str,
        tool_result: ToolResult
    ) -> None:
        """Record tool execution in database."""
        await self.results_collection.insert_one(tool_result.dict())
        
        session = await self.session_service.get_session(session_id)
        if session:
            session.tool_executions.append(tool_result)
            await self.session_service.update_session(session)

    async def _execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the actual tool implementation."""
        # This would be implemented by specific tool classes
        raise NotImplementedError()
