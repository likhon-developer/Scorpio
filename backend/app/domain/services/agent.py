from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from app.domain.models.agent import Agent, AgentStatus, AgentSkill
from app.domain.models.task import Task, TaskStatus, TaskPriority
from app.infrastructure.database import mongodb_db, redis_client
from app.domain.models.organization import AuditLog

class AgentService:
    async def create_agent(self, agent_data: Dict[str, Any]) -> Agent:
        agent = Agent(**agent_data)
        await mongodb_db.agents.insert_one(agent.dict())
        await self._create_audit_log("create_agent", agent.id, agent.dict())
        return agent
    
    async def get_agent(self, agent_id: UUID) -> Optional[Agent]:
        if agent_data := await mongodb_db.agents.find_one({"id": agent_id}):
            return Agent(**agent_data)
        return None
    
    async def update_agent_status(self, agent_id: UUID, status: AgentStatus) -> Optional[Agent]:
        update = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        if result := await mongodb_db.agents.find_one_and_update(
            {"id": agent_id},
            {"$set": update},
            return_document=True
        ):
            agent = Agent(**result)
            await self._create_audit_log("update_agent_status", agent_id, {"status": status})
            return agent
        return None
    
    async def find_available_agents(self, required_skills: List[AgentSkill]) -> List[Agent]:
        query = {
            "status": AgentStatus.AVAILABLE,
            "skills": {
                "$all": [
                    {
                        "$elemMatch": {
                            "name": skill.name,
                            "level": {"$gte": skill.level}
                        }
                    } for skill in required_skills
                ]
            }
        }
        cursor = mongodb_db.agents.find(query)
        return [Agent(**agent_data) async for agent_data in cursor]
    
    async def allocate_agent(self, task: Task) -> Optional[Agent]:
        # Find available agents with required skills
        available_agents = await self.find_available_agents(task.requirements)
        if not available_agents:
            return None
            
        # Select best agent based on metrics and workload
        best_agent = await self._select_best_agent(available_agents, task)
        if best_agent:
            # Update agent status and assign task
            await self.update_agent_status(best_agent.id, AgentStatus.BUSY)
            return best_agent
        return None
    
    async def _select_best_agent(self, agents: List[Agent], task: Task) -> Optional[Agent]:
        if not agents:
            return None
            
        # Score agents based on multiple criteria
        scored_agents = []
        for agent in agents:
            score = 0
            # Skill match score
            for req in task.requirements:
                agent_skill = next((s for s in agent.skills if s.name == req.name), None)
                if agent_skill:
                    score += (agent_skill.level - req.minimum_level + 1) * 10
                    
            # Performance score
            score += agent.metrics.success_rate * 5
            score -= agent.metrics.average_response_time * 0.1
            
            scored_agents.append((agent, score))
            
        # Return agent with highest score
        return max(scored_agents, key=lambda x: x[1])[0] if scored_agents else None
    
    async def _create_audit_log(self, action: str, resource_id: UUID, details: Dict[str, Any]):
        log = AuditLog(
            actor_id=resource_id,
            actor_type="agent",
            action=action,
            resource_type="agent",
            resource_id=resource_id,
            details=details,
            status="success"
        )
        await mongodb_db.audit_logs.insert_one(log.dict())
