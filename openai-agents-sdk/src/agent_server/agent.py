import asyncio
import os

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams
from databricks.sdk import WorkspaceClient

from agent_server.server import get_obo_workspace_client

sp_workspace_client = WorkspaceClient()
user_workspace_client = get_obo_workspace_client()


async def testing():
    async with MCPServerStreamableHttp(
        params=MCPServerStreamableHttpParams(
            url=f"{os.environ['DATABRICKS_HOST']}/api/2.0/mcp/functions/system/ai",
            headers=sp_workspace_client.config.authenticate(),
        ),
        name="system.ai uc function mcp server",
    ) as mcp_server:
        agent = Agent(
            name="code execution agent",
            instructions="You are a code execution agent. You can execute code and return the results.",
            model="gpt-5-nano",
            mcp_servers=[mcp_server],
        )
        result = await Runner.run(agent, "Add 7 and 22.")
        return result.final_output


print(asyncio.run(testing()))
