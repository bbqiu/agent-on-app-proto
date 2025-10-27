import asyncio
import os
from typing import AsyncGenerator, List, Optional

import mlflow
from agents import Agent, Runner, set_default_openai_client
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams
from databricks.sdk import WorkspaceClient
from httpx import AsyncClient, Auth, Request
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)
from openai import AsyncOpenAI

from agent_server.mcp_manager import MCPServerManager
from agent_server.server import get_obo_workspace_client, invoke, stream

sp_workspace_client = WorkspaceClient()
# openai_client = sp_workspace_client.serving_endpoints.get_open_ai_client()
user_workspace_client = get_obo_workspace_client()


def get_databricks_host_from_env() -> Optional[str]:
    host = os.getenv("DATABRICKS_HOST")
    if host is None or not host.startswith("https://"):
        print(host)
        return host
    return f"https://{host}"


# def _get_async_http_client(workspace_client: WorkspaceClient) -> AsyncClient:
#     class BearerAuth(Auth):
#         def __init__(self, get_headers_func):
#             self.get_headers_func = get_headers_func

#         def auth_flow(self, request: Request) -> Request:
#             auth_headers = self.get_headers_func()
#             request.headers["Authorization"] = auth_headers["Authorization"]
#             yield request

#     databricks_token_auth = BearerAuth(workspace_client.config.authenticate)
#     return AsyncClient(auth=databricks_token_auth)


# openai_client = AsyncOpenAI(
#     base_url=f"{get_databricks_host_from_env()}/serving-endpoints",
#     api_key="no-token",  # Passing in a placeholder to pass validations, this will not be used
#     http_client=_get_async_http_client(sp_workspace_client),
# )

# set_default_openai_client(openai_client)


mcp_manager = MCPServerManager()
mcp_server = mcp_manager.register_server(
    MCPServerStreamableHttp(
        params=MCPServerStreamableHttpParams(
            url=f"{get_databricks_host_from_env()}/api/2.0/mcp/functions/system/ai",
            headers=sp_workspace_client.config.authenticate(),
        ),
        name="system.ai uc function mcp server",
    )
)

agent = Agent(
    name="code execution agent",
    instructions="You are a code execution agent. You can execute code and return the results.",
    model="gpt-5-nano",
    mcp_servers=[mcp_server],
)

mlflow.openai.autolog()


@invoke()
async def invoke(request: dict) -> ResponsesAgentResponse:
    # TODO: should we auto convert to ResponsesAgentRequest if possible?
    async with mcp_manager:
        result = await Runner.run(agent, request.get("input", []))
        return ResponsesAgentResponse(output=[item.to_input_item() for item in result.new_items])


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
