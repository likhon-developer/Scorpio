"""
Base models for the domain layer with support for parallel processing.

This module provides base classes for domain models with built-in support
for concurrent operations, time tracking, and state management.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4
from typing import Dict, Any, Optional, List, TypeVar, Generic
from pydantic import BaseModel, Field
import asyncio
from concurrent.futures import ThreadPoolExecutor
import structlog

logger = structlog.get_logger(__name__)

T = TypeVar('T', bound=BaseModel)

class TimestampedModel(BaseModel):
    """Base model with timestamp tracking."""
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.now(timezone.utc)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class IdentifiedModel(TimestampedModel):
    """Base model with UUID identification."""
    
    id: UUID = Field(default_factory=uuid4)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IdentifiedModel":
        """Create an instance from a dictionary."""
        return cls(**data)


class MetricsModel(BaseModel):
    """Base model for tracking metrics with thread-safe counters."""
    
    last_active: datetime
    success_rate: float = 0.0
    tasks_completed: int = 0
    _lock: asyncio.Lock = None

    def __init__(self, **data):
        super().__init__(**data)
        self._lock = asyncio.Lock()

    async def increment_tasks(self) -> None:
        """Thread-safe increment of tasks completed."""
        async with self._lock:
            self.tasks_completed += 1
            self.last_active = datetime.now(timezone.utc)

    async def update_success_rate(self, success: bool) -> None:
        """Thread-safe update of success rate."""
        async with self._lock:
            total = self.tasks_completed
            if total > 0:
                current_successes = self.success_rate * total
                new_total = total + 1
                self.success_rate = (current_successes + (1 if success else 0)) / new_total


class ConfigurableModel(BaseModel):
    """Base model with configuration and metadata support."""
    
    configuration: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    async def update_config(self, key: str, value: Any) -> None:
        """Thread-safe configuration update."""
        async with asyncio.Lock():
            self.configuration[key] = value

    async def update_metadata(self, key: str, value: Any) -> None:
        """Thread-safe metadata update."""
        async with asyncio.Lock():
            self.metadata[key] = value


class ParallelProcessingMixin:
    """Mixin to add parallel processing capabilities to models."""
    
    _executor: ThreadPoolExecutor = None
    _max_workers: int = 4

    def __init__(self, *args, max_workers: int = 4, **kwargs):
        super().__init__(*args, **kwargs)
        self._max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)

    async def run_in_parallel(self, func, items: List[Any]) -> List[Any]:
        """Execute a function on multiple items in parallel."""
        loop = asyncio.get_event_loop()
        tasks = []
        for item in items:
            task = loop.run_in_executor(self._executor, func, item)
            tasks.append(task)
        return await asyncio.gather(*tasks, return_exceptions=True)

    def __del__(self):
        if self._executor:
            self._executor.shutdown(wait=False)
