import asyncio
import os
from typing import AsyncGenerator, List

from agents import Agent, Runner
from agents.mcp import MCPServerStdio, MCPServerStreamableHttp, MCPServerStreamableHttpParams
from databricks.sdk import WorkspaceClient
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)

from agent_server.server import get_obo_workspace_client, invoke, stream

sp_workspace_client = WorkspaceClient()
user_workspace_client = get_obo_workspace_client()


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
            try:
                await server.cleanup()
            except Exception as e:
                # Handle anyio TaskGroup cancellation issues during cleanup
                print(f"Warning: Error during MCP server cleanup: {e}")
                # Continue cleanup for other servers


# Global instances
mcp_manager = MCPServerManager()

mcp_server = mcp_manager.register_server(
    MCPServerStreamableHttp(
        params=MCPServerStreamableHttpParams(
            url=f"{os.environ['DATABRICKS_HOST']}/api/2.0/mcp/functions/system/ai",
            headers=sp_workspace_client.config.authenticate(),
        ),
        client_session_timeout_seconds=30,
        name="system.ai uc function mcp server",
    )
)

# Global agent instance declared at module level
agent = Agent(
    name="code execution agent",
    instructions="You are a code execution agent. You can execute code and return the results.",
    model="gpt-5-nano",
    mcp_servers=[mcp_server],
)


# async def testing():
#     async with mcp_manager:
#         result = await Runner.run(agent, "Add 7 and 22.")
#         return result.final_output


@invoke()
async def invoke(request: any) -> ResponsesAgentResponse:
    print("Starting invoke function")
    try:
        print("Entering mcp_manager context")
        async with mcp_manager:
            print("Inside mcp_manager context, about to run agent")
            # result = await Runner.run(agent, request.get("input", []))
            result = await Runner.run(agent, "Add 7 and 22.")
            print(f"Agent run completed successfully")
            return ResponsesAgentResponse(
                output=[item.to_input_item() for item in result.new_items]
            )
    except Exception as e:
        print(f"Exception in invoke: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        raise


# Test the invoke function locally
asyncio.run(invoke({"input": ["Add 7 and 22."]}))

# @stream()
# async def stream(request: dict) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
#     async with mcp_manager:
#         # Extract the user input from the responses API request
#         input_messages = request.get("input", [])
#         if input_messages:
#             # Get the last user message
#             user_content = input_messages[-1].get("content", "")
#         else:
#             user_content = "Hello"

#         result = await Runner.run(agent, user_content)

#         # Yield the response in streaming format
#         yield {"output": [{"role": "assistant", "content": result.final_output}]}
