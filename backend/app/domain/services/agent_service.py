"""
Agent service for orchestrating AI agent operations
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator
import structlog
from motor.motor_asyncio import AsyncIOMotorDatabase
import redis.asyncio as redis

from app.domain.models.session import (
    Session, Message, MessageRole, ToolExecution,
    AgentState, SessionStatus
)
from app.domain.external.mcp_client import MCPClientInterface
from app.infrastructure.llm.openai_client import OpenAIClient
from app.infrastructure.llm.anthropic_client import AnthropicClient
from app.infrastructure.llm.gemini_client import GeminiClient

logger = structlog.get_logger(__name__)


class AgentService:
    """Main agent service for handling AI agent operations"""

    def __init__(
        self,
        mongodb: AsyncIOMotorDatabase,
        redis: redis.Redis,
        mcp_client: Optional[MCPClientInterface] = None
    ):
        self.mongodb = mongodb
        self.redis = redis
        self.mcp_client = mcp_client

        # Initialize LLM clients
        self.llm_clients = {
            "openai": OpenAIClient(),
            "anthropic": AnthropicClient(),
            "gemini": GeminiClient()
        }

        self.sessions_collection = mongodb.sessions
        self.agent_states_collection = mongodb.agent_states

    async def create_session(self) -> Session:
        """Create a new agent session"""
        session = Session(
            id=f"session_{datetime.utcnow().timestamp()}_{hash(datetime.utcnow())}",
            title="New Session"
        )

        await self.sessions_collection.insert_one(session.dict())
        logger.info("Created new session", session_id=session.id)

        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID"""
        doc = await self.sessions_collection.find_one({"id": session_id})
        if doc:
            return Session(**doc)
        return None

    async def list_sessions(self, limit: int = 50) -> List[Session]:
        """List all sessions"""
        cursor = self.sessions_collection.find().sort("created_at", -1).limit(limit)
        sessions = []
        async for doc in cursor:
            sessions.append(Session(**doc))
        return sessions

    async def update_session(self, session: Session) -> None:
        """Update session in database"""
        session.updated_at = datetime.utcnow()
        await self.sessions_collection.replace_one(
            {"id": session.id},
            session.dict()
        )

    async def delete_session(self, session_id: str) -> bool:
        """Delete session by ID"""
        result = await self.sessions_collection.delete_one({"id": session_id})
        if result.deleted_count > 0:
            # Clean up agent state
            await self.agent_states_collection.delete_one({"session_id": session_id})
            logger.info("Deleted session", session_id=session_id)
            return True
        return False

    async def add_message_to_session(
        self,
        session_id: str,
        role: MessageRole,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Add message to session"""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")

        message = Message(
            id=f"msg_{datetime.utcnow().timestamp()}_{hash(content)}",
            role=role,
            content=content,
            metadata=metadata
        )

        session.messages.append(message)
        session.last_message_at = datetime.utcnow()
        await self.update_session(session)

        logger.info(
            "Added message to session",
            session_id=session_id,
            role=role.value,
            message_length=len(content)
        )

        return message

    async def execute_tool(
        self,
        session_id: str,
        tool_name: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool via MCP"""
        if not self.mcp_client:
            raise ValueError("MCP client not configured")

        logger.info(
            "Executing tool",
            session_id=session_id,
            tool_name=tool_name,
            parameters=parameters
        )

        try:
            result = await self.mcp_client.call_tool(tool_name, parameters)

            # Record tool execution
            tool_execution = ToolExecution(
                id=f"tool_{datetime.utcnow().timestamp()}",
                tool_name=tool_name,
                parameters=parameters,
                result=result,
                status="completed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )

            # Update session with tool execution
            session = await self.get_session(session_id)
            if session:
                session.tool_executions.append(tool_execution)
                await self.update_session(session)

            return result

        except Exception as e:
            logger.error(
                "Tool execution failed",
                session_id=session_id,
                tool_name=tool_name,
                error=str(e)
            )

            # Record failed tool execution
            tool_execution = ToolExecution(
                id=f"tool_{datetime.utcnow().timestamp()}",
                tool_name=tool_name,
                parameters=parameters,
                status="failed",
                error=str(e),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )

            session = await self.get_session(session_id)
            if session:
                session.tool_executions.append(tool_execution)
                await self.update_session(session)

            raise

    async def stream_chat(
        self,
        session_id: str,
        messages: List[Dict[str, str]],
        llm_provider: str = "openai"
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat response with tool execution support"""

        llm_client = self.llm_clients.get(llm_provider)
        if not llm_client:
            raise ValueError(f"LLM provider {llm_provider} not available")

        # Get available tools
        available_tools = []
        if self.mcp_client:
            try:
                mcp_tools = await self.mcp_client.list_tools()
                available_tools = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema
                    }
                    for tool in mcp_tools
                ]
            except Exception as e:
                logger.warning("Failed to get MCP tools", error=str(e))

        # Stream LLM response
        async for chunk in llm_client.stream_chat(messages, available_tools):
            if chunk.get("type") == "tool_call":
                # Execute tool
                tool_call = chunk["data"]
                try:
                    tool_result = await self.execute_tool(
                        session_id,
                        tool_call["name"],
                        tool_call["arguments"]
                    )

                    # Send tool result back to LLM
                    yield {
                        "type": "tool_result",
                        "data": {
                            "tool_call_id": tool_call.get("id"),
                            "result": tool_result
                        }
                    }

                except Exception as e:
                    yield {
                        "type": "error",
                        "data": {
                            "message": f"Tool execution failed: {str(e)}",
                            "tool_name": tool_call["name"]
                        }
                    }

            else:
                # Pass through LLM response
                yield chunk

    async def get_agent_state(self, session_id: str) -> Optional[AgentState]:
        """Get current agent state"""
        doc = await self.agent_states_collection.find_one({"session_id": session_id})
        if doc:
            return AgentState(**doc)
        return None

    async def update_agent_state(
        self,
        session_id: str,
        status: str,
        current_task: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update agent state"""
        state = AgentState(
            session_id=session_id,
            status=status,
            current_task=current_task,
            context=context or {}
        )

        await self.agent_states_collection.replace_one(
            {"session_id": session_id},
            state.dict(),
            upsert=True
        )

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions"""
        # This would be called by a background task
        # Implementation depends on your session expiration policy
        pass
