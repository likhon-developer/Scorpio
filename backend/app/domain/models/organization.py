from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

class TeamType(str, Enum):
    PROJECT = "project"
    FUNCTIONAL = "functional"
    SPECIALIZED = "specialized"
    TEMPORARY = "temporary"

class TeamMetrics(BaseModel):
    total_tasks_completed: int = 0
    active_tasks: int = 0
    success_rate: float = 0.0
    average_response_time: float = 0.0
    collaboration_score: float = 0.0

class Team(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    type: TeamType
    description: Optional[str]
    leader_id: UUID
    members: List[UUID] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metrics: TeamMetrics = Field(default_factory=TeamMetrics)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AuditLog(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor_id: UUID
    actor_type: str  # "human" or "agent"
    action: str
    resource_type: str
    resource_id: UUID
    details: Dict[str, Any]
    ip_address: Optional[str]
    status: str
    changes: Optional[Dict[str, Any]]

class AnalyticsMetric(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    value: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dimensions: Dict[str, str] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Alert(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    type: str
    severity: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str
    affected_resource_id: Optional[UUID]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    status: str = "new"
    resolved_at: Optional[datetime]
    resolved_by: Optional[UUID]
    resolution_notes: Optional[str]
