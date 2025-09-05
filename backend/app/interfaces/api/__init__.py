from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sse_starlette.sse import EventSourceResponse
from typing import List, Optional
from uuid import UUID
from app.domain.services.session import SessionService
from app.domain.services.orchestrator import ToolOrchestrator
from app.domain.models.core import Session, Message, Tool, ToolExecution
from . import automation

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
session_service = SessionService()
tool_orchestrator = ToolOrchestrator()

# Include automation router
router.include_router(
    automation.router,
    prefix="/automation",
    tags=["automation"]
)
