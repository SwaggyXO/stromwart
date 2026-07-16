from typing import Any

from fastapi import APIRouter

from stromwart.application.dependencies import ContainerDep
from stromwart.mcp.server import StromwartMCPServer

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.post("/tools/list")
async def mcp_list_tools() -> dict[str, Any]:
    """MCP tools/list — returns available tool manifest."""
    return {"tools": StromwartMCPServer.TOOLS}


@router.post("/tools/call")
async def mcp_call_tool(request: dict[str, Any], container: ContainerDep) -> dict[str, Any]:
    """MCP tools/call — execute a tool by name."""
    name = request.get("name", "")
    arguments = request.get("arguments", {})
    if not isinstance(arguments, dict):
        arguments = {}
    result = await container.mcp_server.call_tool(str(name), arguments)
    return {"result": result}
