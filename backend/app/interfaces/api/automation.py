from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from app.domain.services.agent import AgentService
from app.domain.services.task import TaskService
from app.domain.services.analytics import AnalyticsService
from app.domain.models.agent import Agent, AgentStatus
from app.domain.models.task import Task, TaskStatus
from app.domain.models.organization import AnalyticsMetric, Alert, AuditLog

router = APIRouter()
agent_service = AgentService()
task_service = TaskService()
analytics_service = AnalyticsService()

# Agent Management Endpoints
@router.post("/agents", response_model=Agent)
async def create_agent(agent_data: dict):
    return await agent_service.create_agent(agent_data)

@router.get("/agents/{agent_id}", response_model=Agent)
async def get_agent(agent_id: UUID):
    if agent := await agent_service.get_agent(agent_id):
        return agent
    raise HTTPException(status_code=404, detail="Agent not found")

@router.patch("/agents/{agent_id}/status")
async def update_agent_status(agent_id: UUID, status: AgentStatus):
    if agent := await agent_service.update_agent_status(agent_id, status):
        return agent
    raise HTTPException(status_code=404, detail="Agent not found")

# Task Management Endpoints
@router.post("/tasks", response_model=Task)
async def create_task(task_data: dict):
    try:
        return await task_service.create_task(task_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: UUID):
    if task := await task_service.get_task(task_id):
        return task
    raise HTTPException(status_code=404, detail="Task not found")

@router.patch("/tasks/{task_id}/status")
async def update_task_status(
    task_id: UUID,
    status: TaskStatus,
    output: Optional[dict] = None,
    error: Optional[str] = None
):
    if task := await task_service.update_task_status(task_id, status, output, error):
        return task
    raise HTTPException(status_code=404, detail="Task not found")

@router.get("/teams/{team_id}/tasks", response_model=List[Task])
async def get_team_tasks(team_id: UUID):
    return await task_service.get_team_tasks(team_id)

# Analytics Endpoints
@router.post("/analytics/metrics")
async def record_metric(metric: AnalyticsMetric):
    await analytics_service.record_metric(metric)
    return {"status": "success"}

@router.get("/analytics/metrics/{metric_name}/history")
async def get_metric_history(
    metric_name: str,
    start_time: datetime,
    end_time: datetime = None,
    dimensions: Optional[dict] = None
):
    if end_time is None:
        end_time = datetime.utcnow()
    return await analytics_service.get_metric_history(
        metric_name,
        start_time,
        end_time,
        dimensions
    )

@router.get("/analytics/metrics/{metric_name}/aggregate")
async def get_aggregate_metrics(
    metric_name: str,
    interval: str = Query(..., regex="^(hourly|daily)$"),
    start_time: datetime,
    end_time: datetime = None
):
    if end_time is None:
        end_time = datetime.utcnow()
    return await analytics_service.calculate_aggregate_metrics(
        metric_name,
        interval,
        start_time,
        end_time
    )

@router.get("/analytics/metrics/{metric_name}/forecast")
async def get_metric_forecast(
    metric_name: str,
    horizon_days: int = Query(7, ge=1, le=30)
):
    return await analytics_service.generate_forecast(metric_name, horizon_days)

# Alert Management Endpoints
@router.post("/alerts", response_model=Alert)
async def create_alert(alert_data: dict):
    return await analytics_service.create_alert(alert_data)

@router.patch("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: UUID,
    resolver_id: UUID,
    resolution_notes: str
):
    if alert := await analytics_service.resolve_alert(alert_id, resolver_id, resolution_notes):
        return alert
    raise HTTPException(status_code=404, detail="Alert not found")

@router.get("/alerts/active", response_model=List[Alert])
async def get_active_alerts():
    return await analytics_service.get_active_alerts()

# Audit Logs Endpoints
@router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(
    start_time: datetime,
    end_time: datetime = None,
    actor_id: Optional[UUID] = None,
    resource_type: Optional[str] = None
):
    if end_time is None:
        end_time = datetime.utcnow()
    return await analytics_service.get_audit_logs(
        start_time,
        end_time,
        actor_id,
        resource_type
    )
