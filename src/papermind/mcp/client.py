import asyncio
import logging
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from papermind.config import settings

logger = logging.getLogger(__name__)

_client: MultiServerMCPClient | None = None
_client_url: str | None = None
_tools: list[Any] | None = None
_tools_lock = asyncio.Lock()


def _get_mcp_client() -> MultiServerMCPClient:
    global _client, _client_url
    url = settings.mcp_papers_url
    if _client is None or _client_url != url:
        logger.info("Connecting MCP papers client to %s", url)
        _client = MultiServerMCPClient({
            "papers": {
                "transport": "streamable_http",
                "url": url,
            }
        })
        _client_url = url
    return _client


async def get_mcp_tools() -> list[Any]:
    global _tools
    if _tools is not None:
        return _tools

    async with _tools_lock:
        if _tools is not None:
            return _tools
        logger.info("Initializing MCP papers tools from %s", settings.mcp_papers_url)
        _tools = await _get_mcp_client().get_tools()
        return _tools


async def get_mcp_tool(name: str) -> Any:
    tool = next((t for t in await get_mcp_tools() if t.name == name), None)
    if tool is None:
        raise RuntimeError(f"{name} tool not found")
    return tool
