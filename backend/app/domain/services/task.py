from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from app.domain.models.task import Task, TaskStatus, TaskPriority, TaskMetrics
from app.domain.models.agent import Agent
from app.domain.services.agent import AgentService
from app.infrastructure.database import mongodb_db, redis_client
from app.domain.models.organization import AuditLog

class TaskService:
    def __init__(self):
        self.agent_service = AgentService()

    async def create_task(self, task_data: Dict[str, Any]) -> Task:
        task = Task(**task_data)
        
        # Check task dependencies
        if task.dependencies:
            for dep_id in task.dependencies:
                dep_task = await self.get_task(dep_id)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    raise ValueError(f"Dependent task {dep_id} not completed")
        
        await mongodb_db.tasks.insert_one(task.dict())
        await self._create_audit_log("create_task", task.id, task.dict())
        
        # Try to allocate an agent immediately
        if not task.assigned_to:
            agent = await self.agent_service.allocate_agent(task)
            if agent:
                task = await self.assign_task(task.id, agent.id)
        
        return task
    
    async def get_task(self, task_id: UUID) -> Optional[Task]:
        if task_data := await mongodb_db.tasks.find_one({"id": task_id}):
            return Task(**task_data)
        return None
    
    async def update_task_status(
        self, 
        task_id: UUID, 
        status: TaskStatus,
        output: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> Optional[Task]:
        update = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if output:
            update["output"] = output
            
        if status == TaskStatus.COMPLETED:
            update["metrics.completion_time"] = datetime.utcnow()
            
        if error:
            update["metrics.error_count"] = await self._increment_error_count(task_id)
            
        if result := await mongodb_db.tasks.find_one_and_update(
            {"id": task_id},
            {"$set": update},
            return_document=True
        ):
            task = Task(**result)
            await self._create_audit_log("update_task_status", task_id, {"status": status})
            
            # If task completed, check and update dependent tasks
            if status == TaskStatus.COMPLETED:
                await self._process_dependent_tasks(task_id)
            
            return task
        return None
    
    async def assign_task(self, task_id: UUID, agent_id: UUID) -> Optional[Task]:
        update = {
            "assigned_to": agent_id,
            "status": TaskStatus.ASSIGNED,
            "updated_at": datetime.utcnow(),
            "metrics.start_time": datetime.utcnow()
        }
        
        if result := await mongodb_db.tasks.find_one_and_update(
            {"id": task_id},
            {"$set": update},
            return_document=True
        ):
            task = Task(**result)
            await self._create_audit_log(
                "assign_task", 
                task_id, 
                {"agent_id": str(agent_id)}
            )
            return task
        return None
    
    async def get_team_tasks(self, team_id: UUID) -> List[Task]:
        cursor = mongodb_db.tasks.find({"team_id": team_id})
        return [Task(**task_data) async for task_data in cursor]
    
    async def _increment_error_count(self, task_id: UUID) -> int:
        result = await mongodb_db.tasks.find_one_and_update(
            {"id": task_id},
            {"$inc": {"metrics.error_count": 1}},
            return_document=True
        )
        return result["metrics"]["error_count"] if result else 1
    
    async def _process_dependent_tasks(self, completed_task_id: UUID):
        # Find tasks that depend on the completed task
        cursor = mongodb_db.tasks.find({"dependencies": completed_task_id})
        async for task_data in cursor:
            task = Task(**task_data)
            # Check if all dependencies are completed
            all_deps_completed = True
            for dep_id in task.dependencies:
                dep_task = await self.get_task(dep_id)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    all_deps_completed = False
                    break
            
            # If all dependencies are completed, try to allocate an agent
            if all_deps_completed and task.status == TaskStatus.PENDING:
                agent = await self.agent_service.allocate_agent(task)
                if agent:
                    await self.assign_task(task.id, agent.id)
    
    async def _create_audit_log(self, action: str, resource_id: UUID, details: Dict[str, Any]):
        log = AuditLog(
            actor_id=resource_id,
            actor_type="system",
            action=action,
            resource_type="task",
            resource_id=resource_id,
            details=details,
            status="success"
        )
        await mongodb_db.audit_logs.insert_one(log.dict())
