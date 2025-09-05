"""
Tool management endpoints for MCP integration
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from app.domain.services.agent_service import AgentService


router = APIRouter()


class ToolExecutionRequest(BaseModel):
    """Tool execution request model"""
    tool_name: str
    parameters: Dict[str, Any]


def get_agent_service(request: Request) -> AgentService:
    """Dependency to get agent service from app state"""
    return request.app.agent_service


@router.get("/list")
async def list_tools(
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """List available tools"""

    try:
        tools = []

        # Get MCP tools if available
        if agent_service.mcp_client:
            mcp_tools = await agent_service.mcp_client.list_tools()
            tools.extend([
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema,
                    "source": "mcp"
                }
                for tool in mcp_tools
            ])

        # Add built-in tools
        built_in_tools = [
            {
                "name": "run_terminal_cmd",
                "description": "Execute a terminal command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The command to execute"
                        },
                        "cwd": {
                            "type": "string",
                            "description": "Working directory for the command"
                        }
                    },
                    "required": ["command"]
                },
                "source": "built-in"
            },
            {
                "name": "read_file",
                "description": "Read file content",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "Start line number (optional)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Number of lines to read (optional)"
                        }
                    },
                    "required": ["file_path"]
                },
                "source": "built-in"
            },
            {
                "name": "search_replace",
                "description": "Search and replace text in a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file"
                        },
                        "old_string": {
                            "type": "string",
                            "description": "Text to replace"
                        },
                        "new_string": {
                            "type": "string",
                            "description": "Replacement text"
                        }
                    },
                    "required": ["file_path", "old_string", "new_string"]
                },
                "source": "built-in"
            }
        ]

        tools.extend(built_in_tools)

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "tools": tools
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "msg": f"Failed to list tools: {str(e)}",
                "data": None
            }
        )


@router.post("/execute")
async def execute_tool(
    request: ToolExecutionRequest,
    session_id: str = None,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Execute a tool"""

    if not session_id:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "msg": "session_id header is required",
                "data": None
            }
        )

    try:
        # Execute tool via agent service
        result = await agent_service.execute_tool(
            session_id,
            request.tool_name,
            request.parameters
        )

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "tool_name": request.tool_name,
                "result": result
            }
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "code": 400,
                "msg": str(e),
                "data": None
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "msg": f"Tool execution failed: {str(e)}",
                "data": None
            }
        )


@router.get("/resources")
async def list_resources(
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """List available MCP resources"""

    try:
        resources = []

        if agent_service.mcp_client:
            mcp_resources = await agent_service.mcp_client.list_resources()
            resources.extend([
                {
                    "uri": resource.uri,
                    "name": resource.name,
                    "description": resource.description,
                    "mime_type": resource.mime_type,
                    "source": "mcp"
                }
                for resource in mcp_resources
            ])

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "resources": resources
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "msg": f"Failed to list resources: {str(e)}",
                "data": None
            }
        )


@router.get("/resources/{uri:path}")
async def read_resource(
    uri: str,
    agent_service: AgentService = Depends(get_agent_service)
) -> dict:
    """Read an MCP resource"""

    try:
        if not agent_service.mcp_client:
            raise HTTPException(
                status_code=404,
                detail={
                    "code": 404,
                    "msg": "MCP client not configured",
                    "data": None
                }
            )

        result = await agent_service.mcp_client.read_resource(uri)

        return {
            "code": 0,
            "msg": "success",
            "data": {
                "uri": uri,
                "content": result
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "code": 500,
                "msg": f"Failed to read resource: {str(e)}",
                "data": None
            }
        )
