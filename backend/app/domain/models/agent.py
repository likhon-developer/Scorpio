"""
Domain models for agent management and orchestration.

This module defines the core data models for managing AI agents in the system,
including their status, skills, metrics, and configuration. These models form
the foundation for agent-based task automation and orchestration.

Classes:
    AgentStatus: Enumeration of possible agent operational states
    AgentSkill: Model representing an agent's capability in a specific area
    AgentMetrics: Collection of performance metrics for an agent
    Agent: Core model representing an AI agent in the system
"""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from uuid import UUID, uuid4

class AgentStatus(str, Enum):
    """
    Enumeration of possible operational states for an agent.

    Attributes:
        AVAILABLE (str): Agent is ready to accept new tasks
        BUSY (str): Agent is currently processing a task
        OFFLINE (str): Agent is not currently connected or accessible
        MAINTENANCE (str): Agent is undergoing updates or maintenance
        ERROR (str): Agent has encountered an error state
    """
    AVAILABLE = "available"
    BUSY = "busy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class AgentSkill(BaseModel):
    """
    Represents a specific capability or competency of an agent.

    Attributes:
        name (str): Name of the skill or capability
        level (int): Proficiency level from 1-10, where 10 is highest expertise
        description (Optional[str]): Detailed description of the skill

    Note:
        The level field is constrained to values between 1 and 10 inclusive.
    """
    name: str
    level: int = Field(ge=1, le=10)
    description: Optional[str] = None

class AgentMetrics(BaseModel):
    """
    Collection of performance metrics for tracking agent effectiveness.

    Attributes:
        tasks_completed (int): Total number of tasks successfully completed
        success_rate (float): Percentage of tasks completed successfully
        average_response_time (float): Average time to complete tasks
        last_active (Optional[datetime]): Timestamp of last agent activity
        uptime_percentage (float): Percentage of time agent was available
    """
    tasks_completed: int = 0
    success_rate: float = 0.0
    average_response_time: float = 0.0
    last_active: Optional[datetime]
    uptime_percentage: float = 0.0

class Agent(BaseModel):
    """
    Core model representing an AI agent in the system.

    This class defines the fundamental properties and characteristics of an
    AI agent, including its identification, capabilities, current state,
    and performance metrics.

    Attributes:
        id (UUID): Unique identifier for the agent
        name (str): Human-readable name of the agent
        status (AgentStatus): Current operational state
        skills (List[AgentSkill]): List of agent capabilities
        team_id (Optional[UUID]): ID of the team the agent belongs to
        metrics (AgentMetrics): Performance metrics for the agent
        configuration (Dict[str, Any]): Agent-specific configuration settings
        created_at (datetime): Timestamp when agent was created
        updated_at (datetime): Timestamp of last agent update
        last_health_check (Optional[datetime]): Timestamp of last health check
        version (str): Version identifier of the agent
        security_clearance (str): Security access level of the agent

    Note:
        The agent ID is automatically generated using UUID4 if not provided.
        The status defaults to AVAILABLE when creating a new agent.
        The security_clearance defaults to "standard" if not specified.
    """
    id: UUID = Field(default_factory=uuid4)
    name: str
    status: AgentStatus = AgentStatus.AVAILABLE
    skills: List[AgentSkill] = []
    team_id: Optional[UUID] = None
    metrics: AgentMetrics = Field(default_factory=lambda: AgentMetrics(last_active=datetime.now(timezone.utc)))
    configuration: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_health_check: Optional[datetime] = None
    version: str
    security_clearance: str = "standard"
