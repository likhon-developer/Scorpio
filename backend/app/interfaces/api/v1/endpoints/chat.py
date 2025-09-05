"""
Chat endpoints with SSE streaming
"""

import json
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.domain.services.agent_service import AgentService
from app.domain.models.session import MessageRole


router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model"""
    role: str
    content: str


class ChatRequest(BaseModel):
    """Chat request model"""
    messages: List[ChatMessage]
    llm_provider: str = "openai"


def get_agent_service(request: Request) -> AgentService:
    """Dependency to get agent service from app state"""
    return request.app.agent_service


@router.post("/sse")
async def stream_chat_sse(
    request: Request,
    chat_request: ChatRequest,
    session_id: str = None,
    agent_service: AgentService = Depends(get_agent_service)
):
    """Stream chat response using Server-Sent Events"""

    if not session_id:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "msg": "session_id header is required",
                "data": None
            }
        )

    # Validate session exists
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

    # Convert messages to dict format
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in chat_request.messages
    ]

    # Add system message if not present
    if not any(msg["role"] == "system" for msg in messages):
        messages.insert(0, {
            "role": "system",
            "content": "You are an AI software engineer assistant. Help the user with coding tasks, debugging, and development."
        })

    async def generate_events():
        """Generate SSE events"""

        # Update agent state
        await agent_service.update_agent_state(
            session_id,
            "thinking",
            "Processing user request"
        )

        try:
            async for event in agent_service.stream_chat(
                session_id,
                messages,
                chat_request.llm_provider
            ):
                # Format event for SSE
                event_data = {
                    "type": event["type"],
                    "data": event["data"]
                }

                yield f"data: {json.dumps(event_data)}\n\n"

                # Handle specific event types
                if event["type"] == "token":
                    # Add token to assistant message in session
                    pass  # This would be handled by accumulating tokens

                elif event["type"] == "tool_result":
                    # Add tool result message to session
                    await agent_service.add_message_to_session(
                        session_id,
                        MessageRole.TOOL,
                        f"Tool result: {json.dumps(event['data'], indent=2)}"
                    )

                elif event["type"] == "error":
                    # Update agent state to error
                    await agent_service.update_agent_state(
                        session_id,
                        "error",
                        f"Error: {event['data']}"
                    )

                elif event["type"] == "done":
                    # Update agent state to idle
                    await agent_service.update_agent_state(
                        session_id,
                        "idle"
                    )

        except Exception as e:
            error_event = {
                "type": "error",
                "data": str(e)
            }
            yield f"data: {json.dumps(error_event)}\n\n"

            # Update agent state
            await agent_service.update_agent_state(
                session_id,
                "error",
                str(e)
            )

        # Send completion event
        yield "data: [DONE]\n\n"

    return EventSourceResponse(generate_events())


@router.post("/{session_id}/message", response_model=dict)
async def send_message(
    session_id: str,
    chat_request: ChatRequest,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Send a message to a session (non-streaming)"""

    # Validate session exists
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

    # Add user message to session
    user_message = await agent_service.add_message_to_session(
        session_id,
        MessageRole.USER,
        chat_request.messages[-1].content if chat_request.messages else ""
    )

    # Convert messages to dict format
    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in chat_request.messages
    ]

    # Get LLM response (non-streaming)
    llm_client = agent_service.llm_clients.get(chat_request.llm_provider)
    if not llm_client:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "msg": f"LLM provider {chat_request.llm_provider} not available",
                "data": None
            }
        )

    response = await llm_client.chat_completion(messages)

    # Add assistant message to session
    assistant_message = await agent_service.add_message_to_session(
        session_id,
        MessageRole.ASSISTANT,
        response.get("content", "")
    )

    return {
        "code": 0,
        "msg": "success",
        "data": {
            "message_id": assistant_message.id,
            "content": assistant_message.content,
            "timestamp": assistant_message.timestamp.isoformat()
        }
    }
