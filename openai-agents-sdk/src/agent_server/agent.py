import asyncio
from typing import AsyncGenerator, List, Optional

import mlflow
from agents import Agent, Runner, set_default_openai_api, set_default_openai_client
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams
from databricks.sdk import WorkspaceClient
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)

from agent_server.server import get_obo_workspace_client, invoke, stream
from agent_server.utils import (
    MCPServerManager,
    get_async_openai_client,
    get_databricks_host_from_env,
)

sp_workspace_client = WorkspaceClient()
user_workspace_client = get_obo_workspace_client()
databricks_openai_client = get_async_openai_client(sp_workspace_client)
set_default_openai_client(databricks_openai_client)
set_default_openai_api("chat_completions")
mlflow.openai.autolog()


mcp_manager = MCPServerManager()
mcp_server = mcp_manager.register_server(
    MCPServerStreamableHttp(
        params=MCPServerStreamableHttpParams(
            url=f"{get_databricks_host_from_env()}/api/2.0/mcp/functions/system/ai",
            headers=sp_workspace_client.config.authenticate(),
        ),
        client_session_timeout_seconds=10,
        name="system.ai uc function mcp server",
    )
)

agent = Agent(
    name="code execution agent",
    instructions="You are a code execution agent. You can execute code and return the results.",
    model="gpt-5",
    mcp_servers=[mcp_server],
)


@invoke()
async def invoke(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    async with mcp_manager:
        messages = [i.model_dump() for i in request.input]
        result = await Runner.run(agent, messages)
        return ResponsesAgentResponse(output=[item.to_input_item() for item in result.new_items])


# @stream()
# async def stream(request: dict) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
#     async with mcp_manager:
#         result = await Runner.run(agent, request.get("input", []))

#         # Yield the response in streaming format
#         yield {"output": [{"role": "assistant", "content": result.final_output}]}
