from typing import AsyncGenerator

import mlflow
from databricks.sdk import WorkspaceClient
from databricks_langchain import ChatDatabricks
from langchain.agents import create_agent
from langchain.messages import AIMessageChunk
from langchain_mcp_adapters.client import MultiServerMCPClient
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    create_text_delta,
    output_to_responses_items_stream,
    to_chat_completions_input,
)

from agent_server.server import get_obo_workspace_client, invoke, stream
from agent_server.utils import get_databricks_host_from_env

mlflow.langchain.autolog()
sp_workspace_client = WorkspaceClient()


def init_mcp_client(workspace_client: WorkspaceClient) -> MultiServerMCPClient:
    return MultiServerMCPClient(
        {
            "system.ai": {
                "transport": "streamable_http",
                "url": f"{get_databricks_host_from_env()}/api/2.0/mcp/functions/system/ai",
                "headers": workspace_client.config.authenticate(),
            },
        }
    )


async def init_agent():
    mcp_client = init_mcp_client(sp_workspace_client)
    tools = await mcp_client.get_tools()
    return create_agent(tools=tools, model=ChatDatabricks(endpoint="databricks-claude-3-7-sonnet"))


@invoke()
async def non_streaming(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    # obo_workspace_client = get_obo_workspace_client()
    agent = await init_agent()
    messages = {"messages": to_chat_completions_input([i.model_dump() for i in request.input])}

    result = await agent.ainvoke(input=messages)
    return result


@stream()
async def streaming(
    request: ResponsesAgentRequest,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    # obo_workspace_client = get_obo_workspace_client()
    agent = await init_agent()
    messages = {"messages": to_chat_completions_input([i.model_dump() for i in request.input])}

    async for event in agent.astream(input=messages, stream_mode=["updates", "messages"]):
        if event[0] == "updates":
            for node_data in event[1].values():
                if len(node_data.get("messages", [])) > 0:
                    for item in output_to_responses_items_stream(node_data["messages"]):
                        yield item
        # filter the streamed messages to just the generated text messages
        elif event[0] == "messages":
            try:
                chunk = event[1][0]
                if isinstance(chunk, AIMessageChunk) and (content := chunk.content):
                    yield ResponsesAgentStreamEvent(
                        **create_text_delta(delta=content, item_id=chunk.id)
                    )
            except Exception as e:
                print(e)
