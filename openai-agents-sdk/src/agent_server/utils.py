import os
import traceback
from asyncio.exceptions import CancelledError
from typing import List, Optional

from agents.mcp import MCPServerStdio, MCPServerStreamableHttp
from databricks.sdk import WorkspaceClient
from httpx import AsyncClient, Auth, Request
from openai import AsyncOpenAI


# TODO: somehow refresh auth for broken connections. gave up here and just reinitialized the agent on each call, which is bad for latency, but what you'd have to do for OBO anyways?)
# some tools that are not OBO should be able to persist across invocations of the agent to save time
class DatabricksMCPServerStreamableHttp(MCPServerStreamableHttp):
    def __init__(self, workspace_client: WorkspaceClient, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.workspace_client = workspace_client

    async def connect(self):
        try:
            return await super().connect()
        except CancelledError:
            print(self.workspace_client.config.authenticate())
            self.params["headers"] = self.workspace_client.config.authenticate() | self.params.get(
                "headers", {}
            )
            print("headers heeeere", self.params["headers"])
            return await super().connect()


# from https://github.com/openai/openai-agents-python/issues/1881
# TODO: refresh the auth for mcp servers when the token is going to expire
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
        async with mcp_manager: ########### somehow will need to handle auth refresh?
                                            maybe this is just handled by a subclass of MCPServerStreamableHttp for databricks
            result = await Runner.run(agent, message)
    """

    def __init__(self, workspace_client: Optional[WorkspaceClient] = None):
        self.workspace_client = workspace_client
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


def get_databricks_host_from_env() -> Optional[str]:
    host = os.getenv("DATABRICKS_HOST")
    if host.startswith("https://"):
        return host
    elif host is not None:
        return f"https://{host}"
    try:
        w = WorkspaceClient()
        return w.config.host
    except Exception as e:
        print(e)
        return None


def _get_async_http_client(workspace_client: WorkspaceClient) -> AsyncClient:
    class BearerAuth(Auth):
        def __init__(self, get_headers_func):
            self.get_headers_func = get_headers_func

        def auth_flow(self, request: Request) -> Request:
            auth_headers = self.get_headers_func()
            request.headers["Authorization"] = auth_headers["Authorization"]
            yield request

    databricks_token_auth = BearerAuth(workspace_client.config.authenticate)
    return AsyncClient(auth=databricks_token_auth)


def get_async_openai_client(workspace_client: WorkspaceClient) -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=f"{get_databricks_host_from_env()}/serving-endpoints",
        api_key="no-token",  # Passing in a placeholder to pass validations, this will not be used
        http_client=_get_async_http_client(workspace_client),
    )
