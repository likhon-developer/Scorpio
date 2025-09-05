"""
Scorpio AI Agent System - Backend API
FastAPI application with MCP integration and real-time streaming
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
from motor.motor_asyncio import AsyncIOMotorClient
import redis.asyncio as redis

from app.core.config import settings
from app.core.logging import setup_logging
from app.interfaces.api.v1.routes import router as api_v1_router
from app.infrastructure.database import init_db
from app.infrastructure.cache import init_cache
from app.domain.services.agent_service import AgentService

# Configure structured logging
setup_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Scorpio AI Agent System")

    # Initialize database connections
    app.mongodb_client = AsyncIOMotorClient(settings.MONGODB_URL)
    app.mongodb = app.mongodb_client[settings.MONGODB_DATABASE]

    # Initialize Redis cache
    app.redis = redis.from_url(settings.REDIS_URL)

    # Initialize services
    app.agent_service = AgentService(
        mongodb=app.mongodb,
        redis=app.redis
    )

    # Initialize database and cache
    await init_db(app.mongodb)
    await init_cache(app.redis)

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Shutting down Scorpio AI Agent System")

    # Close database connections
    app.mongodb_client.close()
    await app.redis.close()

    logger.info("Application shutdown complete")


def create_application() -> FastAPI:
    """Create FastAPI application instance"""

    app = FastAPI(
        title="Scorpio AI Agent System",
        description="Multi-component RAG system with Docker sandboxing",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "msg": "Internal server error",
                "data": None
            }
        )

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "code": 0,
            "msg": "healthy",
            "data": {
                "status": "ok",
                "version": "1.0.0"
            }
        }

    # Include API routes
    app.include_router(
        api_v1_router,
        prefix="/api/v1",
        tags=["v1"]
    )

    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None  # Use our custom logging
    )
