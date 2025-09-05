"""
Domain models for session management
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class SessionStatus(str, Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
    ERROR = "error"


class MessageRole(str, Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class Message(BaseModel):
    """Chat message model"""
    id: str = Field(..., description="Unique message identifier")
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class ToolExecution(BaseModel):
    """Tool execution record"""
    id: str
    tool_name: str
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class Session(BaseModel):
    """Agent session model"""
    id: str = Field(..., description="Unique session identifier")
    title: str = Field(default="New Session", description="Session title")
    status: SessionStatus = SessionStatus.ACTIVE
    messages: List[Message] = Field(default_factory=list)
    tool_executions: List[ToolExecution] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentState(BaseModel):
    """Agent execution state"""
    session_id: str
    current_task: Optional[str] = None
    status: str = "idle"  # idle, thinking, executing, error
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = Field(default_factory=dict)
