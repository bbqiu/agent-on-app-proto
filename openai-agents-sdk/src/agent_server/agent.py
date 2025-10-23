import asyncio
import os

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams
from databricks.sdk import WorkspaceClient

from agent_server.server import create_server, invoke, parse_server_args, stream
from agent_server.utils import get_obo_workspace_client, setup_mlflow

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

# ###########################################
# # Required components to start the server #
# ###########################################

# agent_server = create_server("agent/v1/responses")
# app = agent_server.app


# def main():
#     args = parse_server_args()

#     setup_mlflow()
#     print(
#         f"Single endpoint: POST /invocations on port {args.port} with {args.workers} workers and reload: {args.reload}"
#     )

#     agent_server.run(
#         "agent_server.agent:app",  # import string for app defined above to support workers
#         port=args.port,
#         workers=args.workers,
#         reload=args.reload,
#     )
