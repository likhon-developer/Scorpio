from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from uuid import UUID, uuid4

class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskStatus(str, Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"

class TaskType(str, Enum):
    AUTOMATION = "automation"
    ANALYSIS = "analysis"
    INTEGRATION = "integration"
    MAINTENANCE = "maintenance"
    SECURITY = "security"
    COLLABORATION = "collaboration"

class TaskMetrics(BaseModel):
    start_time: Optional[datetime]
    completion_time: Optional[datetime]
    duration: Optional[float]
    retries: int = 0
    error_count: int = 0
    resources_used: Dict[str, float] = Field(default_factory=dict)

class TaskRequirement(BaseModel):
    skill_name: str
    minimum_level: int = Field(ge=1, le=10)
    preferred_level: Optional[int] = Field(None, ge=1, le=10)

class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str
    type: TaskType
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deadline: Optional[datetime]
    assigned_to: Optional[UUID]
    created_by: UUID
    team_id: Optional[UUID]
    requirements: List[TaskRequirement] = []
    dependencies: List[UUID] = []
    metrics: TaskMetrics = Field(default_factory=TaskMetrics)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]]
    review_status: Optional[str]
    reviewer_id: Optional[UUID]
