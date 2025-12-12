"""
OpenAI Agents SDK agent with short-term memory support.

This module implements a code execution agent with thread-scoped conversation
history stored in PostgreSQL for stateful multi-turn conversations.
"""

from typing import AsyncGenerator, Optional

import mlflow
from agents import Agent, Runner, set_default_openai_api, set_default_openai_client
from agents.tracing import set_trace_processors
from databricks_openai import AsyncDatabricksOpenAI
from databricks_openai.agents import McpServer
from mlflow.genai.agent_server import invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
)

from agent_server.session import get_session
from agent_server.utils import (
    get_databricks_host_from_env,
    get_user_workspace_client,
    process_agent_stream_events,
)

# NOTE: this will work for all databricks models OTHER than GPT-OSS, which uses a slightly different API
set_default_openai_client(AsyncDatabricksOpenAI())
set_default_openai_api("chat_completions")
set_trace_processors([])  # only use mlflow for trace processing
mlflow.openai.autolog()


async def init_mcp_server():
    return McpServer(
        url=f"{get_databricks_host_from_env()}/api/2.0/mcp/functions/system/ai",
        name="system.ai uc function mcp server",
    )


def create_coding_agent(mcp_server: McpServer) -> Agent:
    return Agent(
        name="code execution agent",
        instructions="You are a code execution agent. You can execute code and return the results.",
        model="databricks-claude-3-7-sonnet",
        mcp_servers=[mcp_server],
    )


def extract_thread_id(request: ResponsesAgentRequest) -> Optional[str]:
    """Extract thread_id from custom_inputs if present."""
    if hasattr(request, "custom_inputs") and request.custom_inputs:
        return request.custom_inputs.get("thread_id")
    return None


def extract_latest_user_message(request: ResponsesAgentRequest) -> str:
    """
    Extract the latest user message content as a string.
    
    When using session memory, the OpenAI Agents SDK expects a string input
    (the new user message), not a list. The session handles conversation history.
    """
    # Find the last user message in the input
    for item in reversed(request.input):
        item_dict = item.model_dump()
        if item_dict.get("role") == "user":
            content = item_dict.get("content")
            # Handle both string content and structured content
            if isinstance(content, str):
                return content
            elif isinstance(content, list):
                # Extract text from structured content (e.g., [{"type": "input_text", "text": "..."}])
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") in ("input_text", "text"):
                            return part.get("text", "")
                        elif "text" in part:
                            return part["text"]
    return ""


@invoke()
async def invoke(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    """
    Handle non-streaming agent invocation with short-term memory.
    
    Supports thread_id in custom_inputs for conversation continuity:
    - If thread_id is provided, continues the existing conversation
    - If not provided, creates a new thread and returns thread_id in custom_outputs
    """
    # Optionally use the user's workspace client for on-behalf-of authentication
    # user_workspace_client = get_user_workspace_client()
    
    thread_id = extract_thread_id(request)
    
    async with await init_mcp_server() as mcp_server:
        agent = create_coding_agent(mcp_server)
        user_message = extract_latest_user_message(request)
        session, resolved_thread_id = await get_session(thread_id)
        result = await Runner.run(agent, user_message, session=session)
        return ResponsesAgentResponse(
            output=[item.to_input_item() for item in result.new_items],
            custom_outputs={"thread_id": resolved_thread_id},
        )


@stream()
async def stream(request: ResponsesAgentRequest) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    """
    Handle streaming agent invocation with short-term memory.
    
    Supports thread_id in custom_inputs for conversation continuity:
    - If thread_id is provided, continues the existing conversation
    - If not provided, creates a new thread and returns thread_id in custom_outputs
    """
    # Optionally use the user's workspace client for on-behalf-of authentication
    # user_workspace_client = get_user_workspace_client()
    
    thread_id = extract_thread_id(request)
    
    async with await init_mcp_server() as mcp_server:
        agent = create_coding_agent(mcp_server)
        
        # Extract the latest user message as a string for session memory
        user_message = extract_latest_user_message(request)
        
        # Get session for thread-scoped memory
        session, resolved_thread_id = await get_session(thread_id)
        
        # Run the agent with streaming and session for short-term memory
        result = Runner.run_streamed(agent, input=user_message, session=session)

        async for event in process_agent_stream_events(result.stream_events()):
            yield event
        
        yield ResponsesAgentStreamEvent(
            type="response.done",
            response={
                "custom_outputs": {"thread_id": resolved_thread_id}
            }
        )
