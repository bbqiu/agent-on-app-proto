# from https://github.com/openai/openai-agents-python/issues/1881
from typing import List

from agents.mcp import MCPServerStdio


class MCPServerManager:
    """
    Manages the lifecycle of stdio MCP servers for multi-agent workflows.

    This wrapper addresses the challenge of managing MCP server connections
    across multiple agents defined in separate files. Instead of wrapping
    each agent declaration in async context managers, register servers once
    and use this manager to handle all connection/cleanup operations.

    Usage:
        # In mcp_server.py:
        mcp_manager = MCPServerManager()
        my_server = mcp_manager.register_server(MCPServerStdio(...))

        # In run.py:
        async with mcp_manager:
            result = await Runner.run(agent, message)
    """

    def __init__(self):
        self.servers: List[MCPServerStdio] = []

    def register_server(self, server: MCPServerStdio) -> MCPServerStdio:
        """
        Register an MCP server for lifecycle management.

        Args:
            server: The MCPServerStdio instance to manage

        Returns:
            The same server instance (for convenience)
        """
        if server not in self.servers:
            self.servers.append(server)
        return server

    async def __aenter__(self):
        """Connect all registered servers when entering async context."""
        await self.connect_all()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup all registered servers when exiting async context."""
        await self.cleanup_all()
        return False  # Don't suppress exceptions

    async def connect_all(self):
        """Explicitly connect all registered servers."""
        for server in self.servers:
            await server.connect()

    async def cleanup_all(self):
        """Explicitly cleanup all registered servers."""
        for server in self.servers:
            await server.cleanup()
