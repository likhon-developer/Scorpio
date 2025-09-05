from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class Session(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    title: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class Tool(BaseModel):
    name: str
    description: str
    parameters: Dict[str, Any]
    is_async: bool = False
    requires_sandbox: bool = False

class ToolExecution(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    tool_name: str
    parameters: Dict[str, Any]
    status: str
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime]
