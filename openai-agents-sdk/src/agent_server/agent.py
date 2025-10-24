import os
from typing import AsyncGenerator

from agents import Agent, Runner
from agents.mcp import MCPServerStreamableHttp, MCPServerStreamableHttpParams
from databricks.sdk import WorkspaceClient
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)

from agent_server.server import get_obo_workspace_client, invoke, stream

sp_workspace_client = WorkspaceClient()
user_workspace_client = get_obo_workspace_client()

# Global agent and MCP server instances
mcp_server = None
agent = None


async def initialize_agent():
    global mcp_server, agent
    if agent is None:
        mcp_server = MCPServerStreamableHttp(
            params=MCPServerStreamableHttpParams(
                url=f"{os.environ['DATABRICKS_HOST']}/api/2.0/mcp/functions/system/ai",
                headers=sp_workspace_client.config.authenticate(),
            ),
            name="system.ai uc function mcp server",
        )
        await mcp_server.__aenter__()

        agent = Agent(
            name="code execution agent",
            instructions="You are a code execution agent. You can execute code and return the results.",
            model="gpt-5-nano",
            mcp_servers=[mcp_server],
        )
    return agent


async def testing():
    agent = await initialize_agent()
    result = await Runner.run(agent, "Add 7 and 22.")
    return result.final_output


@invoke()
async def invoke(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    agent = await initialize_agent()

    # result = await Runner.run(agent, request.input)
    result = await Runner.run(agent, "Add 7 and 22.")
    print(result.model_dump())
    return result
    # return ResponsesAgentResponse(output=[{"role": "assistant", "content": result.final_output}])


@stream()
async def stream(request: dict) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    agent = await initialize_agent()

    # Extract the user input from the responses API request
    input_messages = request.get("input", [])
    if input_messages:
        # Get the last user message
        user_content = input_messages[-1].get("content", "")
    else:
        user_content = "Hello"

    result = await Runner.run(agent, user_content)

    # Yield the response in streaming format
    yield {"output": [{"role": "assistant", "content": result.final_output}]}
