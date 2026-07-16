from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class MCPToolDef:
    name: str
    description: str
    input_schema: dict[str, Any]
    server_url: str


class MCPToolClient:
    """
    MCP client for consuming external tools via standard protocol.
    Agents use this to call Prometheus, Grafana, CDN APIs, etc.
    """

    def __init__(self, servers: list[dict[str, str]] | None = None) -> None:
        self._servers = servers or []
        self._tools: dict[str, MCPToolDef] = {}
        self._client = httpx.AsyncClient(timeout=30.0)

    async def discover_tools(self) -> list[MCPToolDef]:
        """Discover tools from all registered MCP servers."""
        all_tools: list[MCPToolDef] = []

        for server in self._servers:
            url = server.get("url", "")
            try:
                resp = await self._client.post(f"{url}/tools/list", json={})
                resp.raise_for_status()
                data = resp.json()
                for tool in data.get("tools", []):
                    tool_def = MCPToolDef(
                        name=tool["name"],
                        description=tool.get("description", ""),
                        input_schema=tool.get("inputSchema", {}),
                        server_url=url,
                    )
                    self._tools[tool_def.name] = tool_def
                    all_tools.append(tool_def)
            except Exception:
                continue

        return all_tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call an external tool via MCP protocol."""
        tool_def = self._tools.get(name)
        if tool_def is None:
            return {"error": f"tool '{name}' not found in registry"}

        try:
            resp = await self._client.post(
                f"{tool_def.server_url}/tools/call",
                json={"name": name, "arguments": arguments},
            )
            resp.raise_for_status()
            result = resp.json().get("result", {})
            return result if isinstance(result, dict) else {"result": result}
        except Exception as error:
            return {"error": f"MCP call failed: {type(error).__name__}: {error}"}

    def list_available_tools(self) -> list[dict[str, str]]:
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]

    async def close(self) -> None:
        await self._client.aclose()
