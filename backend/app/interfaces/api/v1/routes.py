"""
API v1 routes for Scorpio AI Agent System
"""

from fastapi import APIRouter
from app.interfaces.api.v1.endpoints import (
    sessions,
    chat,
    files,
    tools
)

# Create main v1 router
api_v1_router = APIRouter()

# Include endpoint routers
api_v1_router.include_router(
    sessions.router,
    prefix="/sessions",
    tags=["sessions"]
)

api_v1_router.include_router(
    chat.router,
    prefix="/chat",
    tags=["chat"]
)

api_v1_router.include_router(
    files.router,
    prefix="/files",
    tags=["files"]
)

api_v1_router.include_router(
    tools.router,
    prefix="/tools",
    tags=["tools"]
)
