import asyncio
import logging
import os
import uuid
from typing import Annotated, Any, AsyncGenerator, Optional, Sequence, TypedDict

import mlflow
from databricks.sdk import WorkspaceClient
from databricks_langchain import (
    ChatDatabricks,
    CheckpointSaver,
    DatabricksMCPServer,
    DatabricksMultiServerMCPClient,
)
from langchain_core.messages import AIMessage, AnyMessage
from langchain_core.runnables import RunnableConfig, RunnableLambda
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt.tool_node import ToolNode
from mlflow.genai.agent_server import invoke, stream
from mlflow.types.responses import (
    ResponsesAgentRequest,
    ResponsesAgentResponse,
    ResponsesAgentStreamEvent,
    to_chat_completions_input,
)

from agent_server.utils import (
    get_databricks_host_from_env,
    get_user_workspace_client,
    process_agent_astream_events,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

mlflow.langchain.autolog()
sp_workspace_client = WorkspaceClient()


############################################
# Define your LLM endpoint and system prompt
############################################
LLM_ENDPOINT_NAME = "databricks-claude-sonnet-4-5"
SYSTEM_PROMPT = """You are a helpful assistant. Use the available tools to answer questions."""

############################################
# Lakebase configuration for statefulness
############################################
LAKEBASE_INSTANCE_NAME = os.getenv("LAKEBASE_INSTANCE_NAME", "")


#####################
# Define agent state
#####################


class AgentState(TypedDict):
    """State for the agent graph."""
    messages: Annotated[Sequence[AnyMessage], add_messages]
    custom_inputs: Optional[dict[str, Any]]
    custom_outputs: Optional[dict[str, Any]]


#####################
# MCP Client and Agent initialization
#####################


def init_mcp_client(workspace_client: WorkspaceClient) -> DatabricksMultiServerMCPClient:
    host_name = get_databricks_host_from_env()
    return DatabricksMultiServerMCPClient(
        [
            DatabricksMCPServer(
                name="system-ai",
                url=f"{host_name}/api/2.0/mcp/functions/system/ai",
            ),
        ]
    )


async def init_agent(
    workspace_client: Optional[WorkspaceClient] = None,
    checkpointer: Optional[Any] = None,
):
    """Initialize the agent with MCP tools and optional checkpointing for statefulness.
    
    Args:
        workspace_client: Optional workspace client for MCP initialization
        checkpointer: Optional CheckpointSaver for conversation persistence
    
    Returns:
        Compiled LangGraph agent
    """
    mcp_client = init_mcp_client(workspace_client or sp_workspace_client)
    tools = await mcp_client.get_tools()
    
    model = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)
    model_with_tools = model.bind_tools(tools) if tools else model

    def should_continue(state: AgentState):
        """Determine if the agent should continue to tools or end."""
        messages = state["messages"]
        last_message = messages[-1]
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            return "continue"
        return "end"

    # Preprocessor to add system prompt
    preprocessor = RunnableLambda(
        lambda state: [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
    )
    model_runnable = preprocessor | model_with_tools

    def call_model(state: AgentState, config: RunnableConfig):
        """Call the model with the current state (sync for CheckpointSaver compatibility)."""
        response = model_runnable.invoke(state, config)
        return {"messages": [response]}

    # Build the workflow graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)

    if tools:
        workflow.add_node("tools", ToolNode(tools))
        workflow.add_conditional_edges(
            "agent", should_continue, {"continue": "tools", "end": END}
        )
        workflow.add_edge("tools", "agent")
    else:
        workflow.add_edge("agent", END)

    workflow.set_entry_point("agent")
    return workflow.compile(checkpointer=checkpointer)


#####################
# Thread ID management for statefulness
#####################


def _get_or_create_thread_id(request: ResponsesAgentRequest) -> str:
    """Get thread_id from request or create a new one.
    
    Priority:
    1. Use thread_id from custom_inputs if present
    2. Use conversation_id from chat context if available
    3. Generate a new UUID
    
    Returns:
        thread_id: The thread identifier to use for this conversation
    """
    ci = dict(request.custom_inputs or {})

    # Check custom_inputs first
    if "thread_id" in ci:
        logger.info(f"Using thread_id from custom_inputs: {ci['thread_id']}")
        return ci["thread_id"]

    # Check conversation_id from chat context
    if request.context and getattr(request.context, "conversation_id", None):
        logger.info(f"Using conversation_id from context: {request.context.conversation_id}")
        return request.context.conversation_id

    # Generate new thread_id
    new_thread_id = str(uuid.uuid4())
    logger.info(f"Generated new thread_id: {new_thread_id}")
    return new_thread_id


#####################
# Invoke and Stream handlers
#####################


@invoke()
async def non_streaming(request: ResponsesAgentRequest) -> ResponsesAgentResponse:
    """Handle non-streaming invocation by collecting all stream events."""
    # Determine thread_id before streaming so we can include it in custom_outputs
    thread_id = _get_or_create_thread_id(request)
    
    # Ensure thread_id is in custom_inputs for the streaming call
    ci = dict(request.custom_inputs or {})
    ci["thread_id"] = thread_id
    request.custom_inputs = ci
    
    outputs = [
        event.item
        async for event in streaming(request)
        if event.type == "response.output_item.done"
    ]
    
    # Include thread_id in custom_outputs so caller knows which thread was used
    custom_outputs = {"thread_id": thread_id}
    return ResponsesAgentResponse(output=outputs, custom_outputs=custom_outputs)


async def _run_sync_stream_in_thread(
    messages: dict,
    checkpoint_config: dict,
    queue: asyncio.Queue,
):
    """Run sync graph.stream() in a thread and push events to an async queue.
    
    CheckpointSaver only implements sync methods, so we use the sync stream()
    and run it in a thread pool to avoid blocking the event loop.
    """
    def _sync_stream():
        try:
            with CheckpointSaver(instance_name=LAKEBASE_INSTANCE_NAME) as checkpointer:
                # Build graph with sync call_model (init_agent is async, so we need sync version here)
                mcp_client = init_mcp_client(sp_workspace_client)
                # Note: get_tools() is async, but we can call it synchronously via asyncio.run in thread
                loop = asyncio.new_event_loop()
                tools = loop.run_until_complete(mcp_client.get_tools())
                loop.close()
                
                model = ChatDatabricks(endpoint=LLM_ENDPOINT_NAME)
                model_with_tools = model.bind_tools(tools) if tools else model

                def should_continue(state: AgentState):
                    msgs = state["messages"]
                    last_message = msgs[-1]
                    if isinstance(last_message, AIMessage) and last_message.tool_calls:
                        return "continue"
                    return "end"

                preprocessor = RunnableLambda(
                    lambda state: [{"role": "system", "content": SYSTEM_PROMPT}] + state["messages"]
                )
                model_runnable = preprocessor | model_with_tools

                def call_model(state: AgentState, config: RunnableConfig):
                    response = model_runnable.invoke(state, config)
                    return {"messages": [response]}

                workflow = StateGraph(AgentState)
                workflow.add_node("agent", call_model)

                if tools:
                    workflow.add_node("tools", ToolNode(tools))
                    workflow.add_conditional_edges(
                        "agent", should_continue, {"continue": "tools", "end": END}
                    )
                    workflow.add_edge("tools", "agent")
                else:
                    workflow.add_edge("agent", END)

                workflow.set_entry_point("agent")
                graph = workflow.compile(checkpointer=checkpointer)

                # Use sync stream()
                for event in graph.stream(
                    messages,
                    checkpoint_config,
                    stream_mode=["updates", "messages"],
                ):
                    queue.put_nowait(("event", event))
                    
            queue.put_nowait(("done", None))
        except Exception as e:
            queue.put_nowait(("error", e))
    
    # Run the sync streaming in a thread pool
    await asyncio.to_thread(_sync_stream)


@stream()
async def streaming(
    request: ResponsesAgentRequest,
) -> AsyncGenerator[ResponsesAgentStreamEvent, None]:
    """Handle streaming invocation with Lakebase checkpointing for conversation history.
    
    Supports statefulness through thread_id:
        - Pass thread_id in custom_inputs to resume a conversation
        - If not provided, uses conversation_id from context or generates a new one
    
    Usage via API:
        # Start a new conversation (auto-generates thread_id)
        curl -X POST http://localhost:8000/invocations \\
            -H "Content-Type: application/json" \\
            -d '{"input": [{"role": "user", "content": "Hello!"}]}'
        
        # Continue an existing conversation
        curl -X POST http://localhost:8000/invocations \\
            -H "Content-Type: application/json" \\
            -d '{
                "input": [{"role": "user", "content": "What did we discuss?"}],
                "custom_inputs": {"thread_id": "your-thread-id-here"}
            }'
    """
    # user_workspace_client = get_user_workspace_client()
    
    # Get or create thread_id for statefulness
    thread_id = _get_or_create_thread_id(request)
    checkpoint_config = {"configurable": {"thread_id": thread_id}}
    
    logger.info(f"Starting async message stream with thread_id: {thread_id}")
    
    messages = {"messages": to_chat_completions_input([i.model_dump() for i in request.input])}

    try:
        # Use a queue to bridge sync streaming to async
        queue: asyncio.Queue = asyncio.Queue()
        
        # Start the sync stream in a background thread
        stream_task = asyncio.create_task(
            _run_sync_stream_in_thread(messages, checkpoint_config, queue)
        )
        
        # Process events from the queue
        while True:
            msg_type, payload = await queue.get()
            
            if msg_type == "done":
                break
            elif msg_type == "error":
                raise payload
            elif msg_type == "event":
                event = payload
                # Process the event using the same logic as process_agent_astream_events
                if event[0] == "updates":
                    from mlflow.types.responses import output_to_responses_items_stream
                    from langchain_core.messages import ToolMessage
                    import json
                    
                    for node_data in event[1].values():
                        if len(node_data.get("messages", [])) > 0:
                            for msg in node_data["messages"]:
                                if isinstance(msg, ToolMessage) and not isinstance(msg.content, str):
                                    msg.content = json.dumps(msg.content)
                            for item in output_to_responses_items_stream(node_data["messages"]):
                                yield item
                elif event[0] == "messages":
                    from langchain_core.messages import AIMessageChunk
                    from mlflow.types.responses import create_text_delta
                    
                    try:
                        chunk = event[1][0]
                        if isinstance(chunk, AIMessageChunk) and (content := chunk.content):
                            yield ResponsesAgentStreamEvent(
                                **create_text_delta(delta=content, item_id=chunk.id)
                            )
                    except Exception as e:
                        logger.exception(f"Error processing stream event: {e}")
        
        # Wait for the stream task to complete
        await stream_task
        
        logger.info(f"Finished async message stream! thread_id: {thread_id}")
    except Exception as e:
        logger.exception(f"Error in streaming for thread_id {thread_id}: {e}")
        raise


#####################
# Lakebase setup
#####################


# ----- Validate configuration -----
if not LAKEBASE_INSTANCE_NAME:
    raise ValueError(
        "LAKEBASE_INSTANCE_NAME is not set. Please set it in the agent.py file or "
        "via the LAKEBASE_INSTANCE_NAME environment variable. "
        "You can create a Lakebase instance in your Databricks workspace."
    )


def _setup_checkpoint_tables():
    """Initialize Lakebase checkpoint tables if they don't exist.
    
    This is idempotent - safe to call multiple times. Tables are only
    created if they don't already exist.
    """
    try:
        logger.info(f"Setting up checkpoint tables for Lakebase instance: {LAKEBASE_INSTANCE_NAME}")
        with CheckpointSaver(instance_name=LAKEBASE_INSTANCE_NAME) as saver:
            saver.setup()
        logger.info("✅ Checkpoint tables are ready.")
    except Exception as e:
        logger.error(f"Failed to setup checkpoint tables: {e}")
        raise RuntimeError(
            f"Could not initialize Lakebase checkpoint tables for instance '{LAKEBASE_INSTANCE_NAME}'. "
            f"Please verify the instance exists and you have proper permissions. Error: {e}"
        ) from e


# Run setup on module load (first import)
_setup_checkpoint_tables()
