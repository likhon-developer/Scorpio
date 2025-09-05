"""
Redis cache initialization and management
"""

import structlog
import redis.asyncio as redis

logger = structlog.get_logger(__name__)


async def init_cache(redis_client: redis.Redis) -> None:
    """Initialize Redis cache"""

    try:
        # Test connection
        await redis_client.ping()
        logger.info("Redis cache connection established")

    except Exception as e:
        logger.error("Failed to connect to Redis", error=str(e))
        raise


async def close_cache_connections(redis_client: redis.Redis) -> None:
    """Close Redis connections"""
    await redis_client.close()
    logger.info("Redis connections closed")
