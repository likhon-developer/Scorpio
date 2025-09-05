from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sse_starlette.sse import EventSourceResponse
from typing import List, Optional
from uuid import UUID
from app.domain.services.session import SessionService
from app.domain.services.orchestrator import ToolOrchestrator
from app.domain.models.core import Session, Message, Tool, ToolExecution

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
session_service = SessionService()
tool_orchestrator = ToolOrchestrator()

# Session Management Endpoints
@router.post("/sessions", response_model=Session)
async def create_session(title: Optional[str] = None, token: str = Depends(oauth2_scheme)):
    return await session_service.create_session(user_id=token, title=title)

@router.get("/sessions/{session_id}", response_model=Session)
async def get_session(session_id: UUID, token: str = Depends(oauth2_scheme)):
    if session := await session_service.get_session(session_id):
        return session
    raise HTTPException(status_code=404, detail="Session not found")

@router.get("/sessions", response_model=List[Session])
async def list_sessions(token: str = Depends(oauth2_scheme)):
    return await session_service.list_user_sessions(user_id=token)

# Chat and Tool Execution Endpoints
@router.post("/sessions/{session_id}/chat")
async def chat_stream(session_id: UUID, message: Message, token: str = Depends(oauth2_scheme)):
    async def event_generator():
        try:
            async for chunk in tool_orchestrator.mcp_client.stream_chat(
                str(session_id),
                [message]
            ):
                yield {
                    "event": "message",
                    "data": chunk
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": str(e)
            }
    
    return EventSourceResponse(event_generator())

@router.post("/sessions/{session_id}/tools/{tool_name}")
async def execute_tool(
    session_id: UUID,
    tool_name: str,
    parameters: dict,
    token: str = Depends(oauth2_scheme)
):
    try:
        execution = await tool_orchestrator.execute_tool(
            session_id=session_id,
            tool_name=tool_name,
            parameters=parameters
        )
        return execution
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}/stream")
async def stream_updates(session_id: UUID, token: str = Depends(oauth2_scheme)):
    async def event_generator():
        try:
            async for update in tool_orchestrator.stream_execution(session_id):
                yield {
                    "event": "tool_update",
                    "data": update
                }
        except Exception as e:
            yield {
                "event": "error",
                "data": str(e)
            }
    
    return EventSourceResponse(event_generator())
