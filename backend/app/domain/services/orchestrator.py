from typing import List, Dict, Any, AsyncGenerator
from uuid import UUID
from datetime import datetime
from app.domain.models.core import Message, Tool, ToolExecution
from app.domain.external.mcp_client import MCPClient
from app.infrastructure.database import mongodb_db, redis_client
import docker
import aiohttp
import json

class ToolOrchestrator:
    def __init__(self):
        self.docker_client = docker.from_env()
        self.mcp_client = MCPClient()
        self.tools: Dict[str, Tool] = {}
        
    def register_tool(self, tool: Tool):
        """Register a new tool with the orchestrator"""
        self.tools[tool.name] = tool
        
    async def execute_tool(self, session_id: UUID, tool_name: str, parameters: Dict[str, Any]) -> ToolExecution:
        """Execute a tool and return its result"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")
            
        tool = self.tools[tool_name]
        execution = ToolExecution(
            session_id=session_id,
            tool_name=tool_name,
            parameters=parameters,
            status="running"
        )
        
        # Save initial execution state
        await mongodb_db.tool_executions.insert_one(execution.dict())
        
        try:
            if tool.requires_sandbox:
                result = await self._execute_in_sandbox(tool, parameters)
            else:
                result = await self._execute_locally(tool, parameters)
                
            execution.status = "completed"
            execution.result = result
            execution.completed_at = datetime.utcnow()
            
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            
        # Update execution state
        await mongodb_db.tool_executions.update_one(
            {"id": execution.id},
            {"$set": execution.dict()}
        )
        
        return execution
    
    async def _execute_in_sandbox(self, tool: Tool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool in an isolated Docker container"""
        container = self.docker_client.containers.run(
            "scorpio-sandbox",
            command=["python", "-m", f"tools.{tool.name}", json.dumps(parameters)],
            detach=True,
            network_mode="none"  # Isolated network
        )
        
        try:
            container.wait(timeout=30)  # 30 second timeout
            logs = container.logs().decode()
            return json.loads(logs)
        finally:
            container.remove(force=True)
            
    async def _execute_locally(self, tool: Tool, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool locally in the main process"""
        # Import and execute tool module directly
        module = __import__(f"app.tools.{tool.name}", fromlist=["execute"])
        result = await module.execute(**parameters)
        return result
        
    async def stream_execution(self, session_id: UUID) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream execution updates for a session"""
        async for execution in mongodb_db.tool_executions.watch(
            pipeline=[{"$match": {"fullDocument.session_id": session_id}}]
        ):
            yield ToolExecution(**execution["fullDocument"]).dict()
