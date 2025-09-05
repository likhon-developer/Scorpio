"""
MCP (Model Context Protocol) client interface
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
import httpx
from pydantic import BaseModel


class MCPTool(BaseModel):
    """MCP Tool definition"""
    name: str
    description: str
    input_schema: Dict[str, Any]


class MCPResource(BaseModel):
    """MCP Resource definition"""
    uri: str
    name: str
    description: str
    mime_type: str


class MCPClientInterface(ABC):
    """Abstract MCP client interface"""

    @abstractmethod
    async def list_tools(self) -> List[MCPTool]:
        """List available MCP tools"""
        pass

    @abstractmethod
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool"""
        pass

    @abstractmethod
    async def list_resources(self) -> List[MCPResource]:
        """List available MCP resources"""
        pass

    @abstractmethod
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read an MCP resource"""
        pass


class HTTPMCPClient(MCPClientInterface):
    """HTTP-based MCP client implementation"""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0)
        )

    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to MCP server"""
        url = f"{self.base_url}{endpoint}"
        headers = {}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = await self.client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response.json()

    async def list_tools(self) -> List[MCPTool]:
        """List available MCP tools"""
        try:
            data = await self._make_request("GET", "/tools")
            return [MCPTool(**tool) for tool in data.get("tools", [])]
        except Exception as e:
            print(f"Failed to list MCP tools: {e}")
            return []

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool"""
        payload = {
            "tool": tool_name,
            "arguments": arguments
        }
        return await self._make_request("POST", "/tools/call", json=payload)

    async def list_resources(self) -> List[MCPResource]:
        """List available MCP resources"""
        try:
            data = await self._make_request("GET", "/resources")
            return [MCPResource(**resource) for resource in data.get("resources", [])]
        except Exception as e:
            print(f"Failed to list MCP resources: {e}")
            return []

    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read an MCP resource"""
        params = {"uri": uri}
        return await self._make_request("GET", "/resources/read", params=params)

    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()
