"""
Session management endpoints
"""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from app.domain.services.agent_service import AgentService
from app.domain.models.session import Session, SessionStatus


router = APIRouter()


class CreateSessionRequest(BaseModel):
    """Request model for creating a session"""
    title: Optional[str] = "New Session"


class UpdateSessionRequest(BaseModel):
    """Request model for updating a session"""
    title: Optional[str] = None
    status: Optional[SessionStatus] = None


def get_agent_service(request: Request) -> AgentService:
    """Dependency to get agent service from app state"""
    return request.app.agent_service


@router.post("", response_model=dict)
async def create_session(
    request: CreateSessionRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Create a new agent session"""

    try:
        session = await agent_service.create_session()

        if request.title and request.title != "New Session":
            session.title = request.title
            await agent_service.update_session(session)

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "session_id": session.id,
                "title": session.title,
                "created_at": session.created_at.isoformat()
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "msg": "Failed to create session",
                "data": None
            }
        )


@router.get("/{session_id}", response_model=dict)
async def get_session(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Get session by ID"""

    session = await agent_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "code": 404,
                "msg": "Session not found",
                "data": None
            }
        )

    return {
        "code": 0,
        "msg": "success",
        "data": {
            "session_id": session.id,
            "title": session.title,
            "status": session.status.value,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in session.messages
            ],
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None
        }
    }


@router.get("", response_model=dict)
async def list_sessions(
    limit: int = 50,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """List all sessions"""

    try:
        sessions = await agent_service.list_sessions(limit)

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "sessions": [
                    {
                        "session_id": session.id,
                        "title": session.title,
                        "status": session.status.value,
                        "created_at": session.created_at.isoformat(),
                        "updated_at": session.updated_at.isoformat(),
                        "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
                        "message_count": len(session.messages),
                        "unread_message_count": 0  # TODO: Implement unread count logic
                    }
                    for session in sessions
                ]
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "msg": "Failed to list sessions",
                "data": None
            }
        )


@router.put("/{session_id}", response_model=dict)
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Update session"""

    session = await agent_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "code": 404,
                "msg": "Session not found",
                "data": None
            }
        )

    # Update fields
    if request.title is not None:
        session.title = request.title

    if request.status is not None:
        session.status = request.status

    await agent_service.update_session(session)

    return {
        "code": 0,
        "msg": "success",
        "data": {
            "session_id": session.id,
            "title": session.title,
            "status": session.status.value
        }
    }


@router.delete("/{session_id}", response_model=dict)
async def delete_session(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Delete session"""

    deleted = await agent_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={
                "code": 404,
                "msg": "Session not found",
                "data": None
            }
        )

    return {
        "code": 0,
        "msg": "success",
        "data": None
    }


@router.post("/{session_id}/stop", response_model=dict)
async def stop_session(
    session_id: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Stop an active session"""

    session = await agent_service.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail={
                "code": 404,
                "msg": "Session not found",
                "data": None
            }
        )

    session.status = SessionStatus.TERMINATED
    await agent_service.update_session(session)

    return {
        "code": 0,
        "msg": "success",
        "data": None
    }
