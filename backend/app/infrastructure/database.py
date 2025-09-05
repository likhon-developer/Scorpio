"""
Database initialization and management
"""

import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = structlog.get_logger(__name__)


async def init_db(mongodb: AsyncIOMotorDatabase) -> None:
    """Initialize database with indexes and collections"""

    try:
        # Create indexes for sessions collection
        await mongodb.sessions.create_index("id", unique=True)
        await mongodb.sessions.create_index("created_at")
        await mongodb.sessions.create_index("updated_at")
        await mongodb.sessions.create_index("last_message_at")

        # Create indexes for agent states collection
        await mongodb.agent_states.create_index("session_id", unique=True)
        await mongodb.agent_states.create_index("last_activity")

        # Create indexes for messages (if stored separately)
        await mongodb.messages.create_index("session_id")
        await mongodb.messages.create_index("timestamp")

        logger.info("Database indexes created successfully")

    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise


async def close_db_connections(mongodb: AsyncIOMotorDatabase) -> None:
    """Close database connections"""
    # Motor handles connection pooling automatically
    # This function is here for consistency and future extensions
    pass
