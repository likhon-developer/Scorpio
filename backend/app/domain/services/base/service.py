"""
Base service classes with support for parallel processing and async operations.

This module provides base service classes with built-in support for:
- Parallel processing using ThreadPoolExecutor
- Async database operations
- Structured logging
- Error handling
- Connection pooling
"""

from typing import TypeVar, Generic, Optional, List, Dict, Any
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from motor.motor_asyncio import AsyncIOMotorDatabase
import structlog
from pydantic import BaseModel
from app.domain.models.base.models import IdentifiedModel
from app.core.exceptions import ServiceError

logger = structlog.get_logger(__name__)
T = TypeVar('T', bound=IdentifiedModel)

class BaseService(Generic[T]):
    """Base service with parallel processing capabilities."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase,
        collection_name: str,
        model_class: type[T],
        max_workers: int = 4
    ):
        self.db = db
        self.collection = db[collection_name]
        self.model_class = model_class
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._bulk_ops_lock = asyncio.Lock()
        
    async def create(self, model: T) -> T:
        """Create a new model instance."""
        try:
            result = await self.collection.insert_one(model.dict())
            logger.info(
                "Created new instance",
                collection=self.collection.name,
                id=str(model.id)
            )
            return model
        except Exception as e:
            logger.error(
                "Failed to create instance",
                collection=self.collection.name,
                error=str(e)
            )
            raise ServiceError(f"Failed to create {self.collection.name}: {str(e)}")

    async def get(self, id: str) -> Optional[T]:
        """Retrieve a model instance by ID."""
        try:
            result = await self.collection.find_one({"id": id})
            return self.model_class(**result) if result else None
        except Exception as e:
            logger.error(
                "Failed to retrieve instance",
                collection=self.collection.name,
                id=id,
                error=str(e)
            )
            raise ServiceError(f"Failed to retrieve {self.collection.name}: {str(e)}")

    async def update(self, model: T) -> T:
        """Update a model instance."""
        try:
            await self.collection.replace_one(
                {"id": str(model.id)},
                model.dict()
            )
            return model
        except Exception as e:
            logger.error(
                "Failed to update instance",
                collection=self.collection.name,
                id=str(model.id),
                error=str(e)
            )
            raise ServiceError(f"Failed to update {self.collection.name}: {str(e)}")

    async def delete(self, id: str) -> bool:
        """Delete a model instance."""
        try:
            result = await self.collection.delete_one({"id": id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(
                "Failed to delete instance",
                collection=self.collection.name,
                id=id,
                error=str(e)
            )
            raise ServiceError(f"Failed to delete {self.collection.name}: {str(e)}")

    async def list(self, filter_dict: Dict[str, Any] = None) -> List[T]:
        """List model instances with optional filtering."""
        try:
            cursor = self.collection.find(filter_dict or {})
            results = await cursor.to_list(length=None)
            return [self.model_class(**doc) for doc in results]
        except Exception as e:
            logger.error(
                "Failed to list instances",
                collection=self.collection.name,
                error=str(e)
            )
            raise ServiceError(f"Failed to list {self.collection.name}: {str(e)}")

    async def bulk_create(self, models: List[T]) -> List[T]:
        """Create multiple model instances in parallel."""
        async with self._bulk_ops_lock:
            try:
                operations = [model.dict() for model in models]
                await self.collection.insert_many(operations)
                return models
            except Exception as e:
                logger.error(
                    "Failed bulk create operation",
                    collection=self.collection.name,
                    count=len(models),
                    error=str(e)
                )
                raise ServiceError(f"Failed bulk create in {self.collection.name}: {str(e)}")

    async def bulk_update(self, models: List[T]) -> List[T]:
        """Update multiple model instances in parallel."""
        async with self._bulk_ops_lock:
            try:
                operations = [
                    (model.id, model.dict())
                    for model in models
                ]
                
                def update_one(op):
                    id_, data = op
                    return self.collection.replace_one({"id": str(id_)}, data)
                
                tasks = [
                    asyncio.create_task(update_one(op))
                    for op in operations
                ]
                await asyncio.gather(*tasks)
                return models
            except Exception as e:
                logger.error(
                    "Failed bulk update operation",
                    collection=self.collection.name,
                    count=len(models),
                    error=str(e)
                )
                raise ServiceError(f"Failed bulk update in {self.collection.name}: {str(e)}")

    async def process_batch(
        self,
        items: List[Any],
        processor_func: callable,
        batch_size: int = 100
    ) -> List[Any]:
        """Process a batch of items in parallel."""
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(*[
                asyncio.create_task(processor_func(item))
                for item in batch
            ])
            results.extend(batch_results)
        return results

    def __del__(self):
        """Cleanup executor on service deletion."""
        if hasattr(self, '_executor'):
            self._executor.shutdown(wait=False)
