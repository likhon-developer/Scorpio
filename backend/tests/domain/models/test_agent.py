"""
Tests for the Agent domain model to ensure backward compatibility and proper functionality.

This test suite verifies that the Agent model and its related models (AgentStatus,
AgentSkill, AgentMetrics) maintain backward compatibility while validating their
core functionality.
"""

import pytest
from datetime import datetime, timezone
from uuid import UUID
from pydantic import ValidationError

from app.domain.models.agent import (
    Agent, 
    AgentStatus, 
    AgentSkill, 
    AgentMetrics
)

# Test Data
SAMPLE_UUID = UUID('12345678-1234-5678-1234-567812345678')
SAMPLE_DATETIME = datetime(2025, 9, 5, tzinfo=timezone.utc)

def test_agent_status_backward_compatibility():
    """Test that all AgentStatus enum values remain valid."""
    assert AgentStatus.AVAILABLE == "available"
    assert AgentStatus.BUSY == "busy"
    assert AgentStatus.OFFLINE == "offline"
    assert AgentStatus.MAINTENANCE == "maintenance"
    assert AgentStatus.ERROR == "error"
    
    # Verify that we can create an agent with any status
    for status in AgentStatus:
        agent = Agent(
            name="TestAgent",
            status=status,
            version="1.0.0",
            metrics=AgentMetrics(last_active=SAMPLE_DATETIME)
        )
        assert agent.status == status

def test_agent_skill_validation():
    """Test AgentSkill model validation and constraints."""
    # Valid skill
    skill = AgentSkill(name="python", level=8, description="Advanced Python programming")
    assert skill.name == "python"
    assert skill.level == 8
    
    # Test level constraints
    with pytest.raises(ValidationError):
        AgentSkill(name="python", level=0)
    with pytest.raises(ValidationError):
        AgentSkill(name="python", level=11)

def test_agent_metrics_defaults():
    """Test that AgentMetrics maintains its default values."""
    metrics = AgentMetrics(last_active=SAMPLE_DATETIME)
    assert metrics.tasks_completed == 0
    assert metrics.success_rate == 0.0
    assert metrics.average_response_time == 0.0
    assert metrics.uptime_percentage == 0.0
    assert metrics.last_active == SAMPLE_DATETIME

def test_agent_backward_compatibility():
    """Test that Agent model maintains backward compatibility with minimal required fields."""
    # Test minimal initialization
    minimal_agent = Agent(
        name="MinimalAgent",
        version="1.0.0",
        metrics=AgentMetrics(last_active=SAMPLE_DATETIME)
    )
    assert minimal_agent.name == "MinimalAgent"
    assert minimal_agent.status == AgentStatus.AVAILABLE
    assert minimal_agent.security_clearance == "standard"
    assert isinstance(minimal_agent.id, UUID)
    assert isinstance(minimal_agent.created_at, datetime)
    assert isinstance(minimal_agent.updated_at, datetime)
    assert minimal_agent.skills == []
    assert minimal_agent.configuration == {}

def test_agent_full_initialization():
    """Test Agent model with all fields populated."""
    skill = AgentSkill(name="python", level=8, description="Advanced Python")
    metrics = AgentMetrics(
        tasks_completed=10,
        success_rate=0.95,
        average_response_time=1.5,
        last_active=SAMPLE_DATETIME,
        uptime_percentage=99.9
    )
    
    agent = Agent(
        id=SAMPLE_UUID,
        name="FullAgent",
        status=AgentStatus.AVAILABLE,
        skills=[skill],
        team_id=SAMPLE_UUID,
        metrics=metrics,
        configuration={"key": "value"},
        created_at=SAMPLE_DATETIME,
        updated_at=SAMPLE_DATETIME,
        last_health_check=SAMPLE_DATETIME,
        version="1.0.0",
        security_clearance="high"
    )
    
    assert agent.id == SAMPLE_UUID
    assert agent.name == "FullAgent"
    assert agent.status == AgentStatus.AVAILABLE
    assert len(agent.skills) == 1
    assert agent.team_id == SAMPLE_UUID
    assert agent.metrics.tasks_completed == 10
    assert agent.configuration == {"key": "value"}
    assert agent.created_at == SAMPLE_DATETIME
    assert agent.version == "1.0.0"
    assert agent.security_clearance == "high"

def test_agent_json_serialization():
    """Test that Agent model can be serialized to and from JSON."""
    agent = Agent(
        name="SerializeAgent",
        version="1.0.0",
        skills=[AgentSkill(name="python", level=8)]
    )
    
    # Convert to JSON and back
    json_data = agent.model_dump_json()
    reconstructed_agent = Agent.model_validate_json(json_data)
    
    assert reconstructed_agent.name == agent.name
    assert reconstructed_agent.version == agent.version
    assert len(reconstructed_agent.skills) == 1
    assert reconstructed_agent.skills[0].name == "python"
